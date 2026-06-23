"""
System and rsyslog statistics.

System metrics are read from /proc — no extra dependencies needed.
CPU% uses a module-level rolling window (two-sample delta), so the first
call after startup returns 0 until a second sample is available.
"""
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse

from .deps import get_current_user, require_role
from .models import UserRole

router = APIRouter(tags=["stats"])

SYSLOG_DATA_DIR = Path("/data/syslog")

# ── CPU rolling delta ─────────────────────────────────────────────────────────

_prev_cpu: dict = {"idle": 0, "total": 0}


def _cpu_percent() -> float:
    try:
        line = Path("/proc/stat").read_text().split("\n")[0]
        vals = list(map(int, line.split()[1:]))
        idle  = vals[3] + (vals[4] if len(vals) > 4 else 0)  # idle + iowait
        total = sum(vals)
        prev  = _prev_cpu.copy()
        _prev_cpu["idle"]  = idle
        _prev_cpu["total"] = total
        d_total = total - prev["total"]
        d_idle  = idle  - prev["idle"]
        if d_total == 0 or prev["total"] == 0:
            return 0.0
        return round((1 - d_idle / d_total) * 100, 1)
    except Exception:
        return -1.0


def _load_avg() -> tuple[float, float, float]:
    try:
        parts = Path("/proc/loadavg").read_text().split()
        return float(parts[0]), float(parts[1]), float(parts[2])
    except Exception:
        return 0.0, 0.0, 0.0


# ── Memory ────────────────────────────────────────────────────────────────────

def _mem_info() -> dict:
    try:
        raw = {}
        for line in Path("/proc/meminfo").read_text().splitlines():
            k, v = line.split(":", 1)
            raw[k.strip()] = int(v.split()[0])  # kB
        total = raw.get("MemTotal", 0)
        avail = raw.get("MemAvailable", raw.get("MemFree", 0))
        used  = total - avail
        pct   = round(used / total * 100, 1) if total else 0.0
        return {
            "total_mb":  round(total  / 1024, 1),
            "used_mb":   round(used   / 1024, 1),
            "avail_mb":  round(avail  / 1024, 1),
            "percent":   pct,
        }
    except Exception:
        return {"total_mb": 0, "used_mb": 0, "avail_mb": 0, "percent": -1.0}


# ── Disk ──────────────────────────────────────────────────────────────────────

def _disk_info(path: str = "/") -> dict:
    try:
        u = shutil.disk_usage(path)
        pct = round(u.used / u.total * 100, 1) if u.total else 0.0
        return {
            "path":      path,
            "total_gb":  round(u.total / 1024**3, 2),
            "used_gb":   round(u.used  / 1024**3, 2),
            "free_gb":   round(u.free  / 1024**3, 2),
            "percent":   pct,
        }
    except Exception:
        return {"path": path, "total_gb": 0, "used_gb": 0, "free_gb": 0, "percent": -1.0}


# ── Events / sec ──────────────────────────────────────────────────────────────

_prev_events: dict = {"count": 0, "ts": 0.0}


def _count_log_lines() -> int:
    """Count total log lines across all syslog files."""
    if not SYSLOG_DATA_DIR.exists():
        return 0
    total = 0
    try:
        for f in SYSLOG_DATA_DIR.rglob("*.log"):
            try:
                total += sum(1 for _ in f.open("rb"))
            except OSError:
                pass
    except Exception:
        pass
    return total


def _events_per_sec() -> float:
    now    = time.monotonic()
    count  = _count_log_lines()
    prev   = _prev_events.copy()
    _prev_events["count"] = count
    _prev_events["ts"]    = now
    elapsed = now - prev["ts"]
    if elapsed < 1 or prev["ts"] == 0.0:
        return 0.0
    delta = max(count - prev["count"], 0)
    return round(delta / elapsed, 2)


# ── rsyslog service meta ──────────────────────────────────────────────────────

def _rsyslog_meta() -> dict:
    """Get queue/drop stats from journalctl impstats output (best-effort)."""
    result = {"queue_size": None, "queue_max": None, "enqueued": None, "dropped": None}
    try:
        out = subprocess.run(
            ["journalctl", "-u", "rsyslog", "--since", "5 minutes ago",
             "--no-pager", "-q"],
            capture_output=True, text=True, timeout=5,
        ).stdout
        for line in out.splitlines():
            if "imuxsock" in line and "origin=imuxsock" not in line:
                continue
            if "origin=core(queue)" in line or "queue.size" in line.lower():
                for part in line.split():
                    if part.startswith("size="):
                        result["queue_size"] = int(part.split("=")[1])
                    elif part.startswith("enqueued="):
                        result["enqueued"] = int(part.split("=")[1])
                    elif part.startswith("full="):
                        result["dropped"] = int(part.split("=")[1])
    except Exception:
        pass
    return result


# ── Combined endpoint ─────────────────────────────────────────────────────────

@router.get("/stats")
async def get_stats(current_user: dict = Depends(get_current_user)):
    load = _load_avg()
    syslog_data_disk = _disk_info(str(SYSLOG_DATA_DIR) if SYSLOG_DATA_DIR.exists() else "/data")
    return {
        "cpu": {
            "percent":   _cpu_percent(),
            "load_1":    load[0],
            "load_5":    load[1],
            "load_15":   load[2],
        },
        "memory":      _mem_info(),
        "disk_root":   _disk_info("/"),
        "disk_syslog": syslog_data_disk,
        "rsyslog": {
            "events_per_sec": _events_per_sec(),
            **_rsyslog_meta(),
        },
    }


# ── Prometheus /metrics ───────────────────────────────────────────────────────

@router.get("/metrics", response_class=PlainTextResponse)
async def prometheus_metrics(current_user: dict = Depends(get_current_user)):
    cpu   = _cpu_percent()
    load  = _load_avg()
    mem   = _mem_info()
    disk  = _disk_info("/")
    slog  = _disk_info(str(SYSLOG_DATA_DIR) if SYSLOG_DATA_DIR.exists() else "/data")
    eps   = _events_per_sec()

    lines = [
        "# HELP rsyslog_manager_cpu_percent CPU utilization percent",
        "# TYPE rsyslog_manager_cpu_percent gauge",
        f"rsyslog_manager_cpu_percent {cpu}",
        "# HELP rsyslog_manager_load_1 Load average 1 min",
        "# TYPE rsyslog_manager_load_1 gauge",
        f"rsyslog_manager_load_1 {load[0]}",
        "# HELP rsyslog_manager_load_5 Load average 5 min",
        "# TYPE rsyslog_manager_load_5 gauge",
        f"rsyslog_manager_load_5 {load[1]}",
        "# HELP rsyslog_manager_load_15 Load average 15 min",
        "# TYPE rsyslog_manager_load_15 gauge",
        f"rsyslog_manager_load_15 {load[2]}",
        "# HELP rsyslog_manager_memory_used_bytes Memory used in bytes",
        "# TYPE rsyslog_manager_memory_used_bytes gauge",
        f"rsyslog_manager_memory_used_bytes {mem['used_mb'] * 1024 * 1024:.0f}",
        "# HELP rsyslog_manager_memory_total_bytes Total memory in bytes",
        "# TYPE rsyslog_manager_memory_total_bytes gauge",
        f"rsyslog_manager_memory_total_bytes {mem['total_mb'] * 1024 * 1024:.0f}",
        "# HELP rsyslog_manager_disk_used_bytes Disk used bytes (root)",
        "# TYPE rsyslog_manager_disk_used_bytes gauge",
        f"rsyslog_manager_disk_used_bytes{{mountpoint=\"/\"}} {disk['used_gb'] * 1024**3:.0f}",
        "# HELP rsyslog_manager_disk_total_bytes Disk total bytes (root)",
        "# TYPE rsyslog_manager_disk_total_bytes gauge",
        f"rsyslog_manager_disk_total_bytes{{mountpoint=\"/\"}} {disk['total_gb'] * 1024**3:.0f}",
        f"rsyslog_manager_disk_used_bytes{{mountpoint=\"/data/syslog\"}} {slog['used_gb'] * 1024**3:.0f}",
        f"rsyslog_manager_disk_total_bytes{{mountpoint=\"/data/syslog\"}} {slog['total_gb'] * 1024**3:.0f}",
        "# HELP rsyslog_events_per_second Estimated log events per second",
        "# TYPE rsyslog_events_per_second gauge",
        f"rsyslog_events_per_second {eps}",
        "",
    ]
    return "\n".join(lines)


# ── Check_MK local check output ───────────────────────────────────────────────

@router.get("/checkmk", response_class=PlainTextResponse)
async def checkmk_output(current_user: dict = Depends(get_current_user)):
    """
    Output in Check_MK local check format:
      <status> <service_name> <perfdata> <summary>
    status: 0=OK 1=WARN 2=CRIT 3=UNKNOWN
    """
    cpu  = _cpu_percent()
    mem  = _mem_info()
    disk = _disk_info("/")
    slog = _disk_info(str(SYSLOG_DATA_DIR) if SYSLOG_DATA_DIR.exists() else "/data")
    eps  = _events_per_sec()
    load = _load_avg()

    def _status(val: float, warn: float, crit: float) -> int:
        if val < 0:       return 3
        if val >= crit:   return 2
        if val >= warn:   return 1
        return 0

    def _row(status: int, name: str, perf: str, summary: str) -> str:
        state = {0: "OK", 1: "WARN", 2: "CRIT", 3: "UNKNOWN"}[status]
        return f"{status} {name} {perf} {state} - {summary}"

    rows = [
        _row(
            _status(cpu, 80, 95),
            "rsyslog_manager_cpu",
            f"cpu_percent={cpu};80;95;0;100",
            f"CPU {cpu}%  Load: {load[0]}/{load[1]}/{load[2]}",
        ),
        _row(
            _status(mem["percent"], 85, 95),
            "rsyslog_manager_memory",
            f"used_mb={mem['used_mb']};{mem['total_mb']*0.85:.0f};{mem['total_mb']*0.95:.0f};0;{mem['total_mb']}",
            f"RAM {mem['used_mb']} MB / {mem['total_mb']} MB ({mem['percent']}%)",
        ),
        _row(
            _status(disk["percent"], 80, 90),
            "rsyslog_manager_disk_root",
            f"used_gb={disk['used_gb']};{disk['total_gb']*0.80:.1f};{disk['total_gb']*0.90:.1f};0;{disk['total_gb']}",
            f"/ {disk['used_gb']} GB / {disk['total_gb']} GB ({disk['percent']}%)",
        ),
        _row(
            _status(slog["percent"], 80, 90),
            "rsyslog_manager_disk_syslog",
            f"used_gb={slog['used_gb']};{slog['total_gb']*0.80:.1f};{slog['total_gb']*0.90:.1f};0;{slog['total_gb']}",
            f"/data/syslog {slog['used_gb']} GB / {slog['total_gb']} GB ({slog['percent']}%)",
        ),
        _row(
            0,
            "rsyslog_manager_events",
            f"events_per_sec={eps};;",
            f"Events/sec: {eps}",
        ),
    ]
    return "\n".join(rows) + "\n"

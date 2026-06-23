import difflib
import io
import json
import re
import shutil
import smtplib
import subprocess
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, List, Optional, Union

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse, StreamingResponse

from .audit import log_action
from .deps import get_current_user, require_role
from .models import UserRole, fake_users_db
from .schemas import RsyslogConfigUpdate

router = APIRouter(prefix="/rsyslog", tags=["rsyslog"])

CONFIG_PATH        = Path("/etc/rsyslog.conf")
CONFIG_BACKUP_PATH = Path("/etc/rsyslog.conf.bak")
HISTORY_DIR        = Path("/etc/rsyslog-manager/history")
MAX_HISTORY        = 10
LOG_SERVICE        = "rsyslog"
SYSLOG_DATA_DIR    = Path("/data/syslog")

_SEV_MAP: Dict[str, int] = {
    "emerg": 0, "emergency": 0,
    "alert": 1,
    "crit": 2, "critical": 2,
    "err": 3, "error": 3,
    "warning": 4, "warn": 4,
    "notice": 5,
    "info": 6, "informational": 6,
    "debug": 7,
}
# Matches unquoted message value at end of JSON object: ..."message": VALUE}
_RE_FIX_MSG = re.compile(r'("message"\s*:\s*)([^"{}\[/][^}]*)\}$')


def run_command(cmd: list[str]) -> str:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Command failed: {' '.join(cmd)} - {exc}",
        )


def get_service_status() -> Dict[str, Union[str, bool]]:
    active = run_command(["systemctl", "is-active", LOG_SERVICE]).strip()
    enabled = run_command(["systemctl", "is-enabled", LOG_SERVICE]).strip()
    version_output = run_command(["rsyslogd", "-v"])
    version_line = version_output.splitlines()[0] if version_output else "unknown"
    version = version_line.replace("rsyslogd ", "") if "rsyslogd" in version_line else version_line
    return {
        "service": LOG_SERVICE,
        "status": active,
        "enabled": enabled == "enabled",
        "version": version,
    }


def get_config_summary() -> Dict[str, Union[str, bool]]:
    if not CONFIG_PATH.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="rsyslog configuration file not found")

    last_modified = datetime.utcfromtimestamp(CONFIG_PATH.stat().st_mtime).isoformat() + "Z"
    content = CONFIG_PATH.read_text(encoding="utf-8", errors="ignore")
    summary = content.splitlines()[0] if content else "No configuration content available."
    return {
        "config_path": str(CONFIG_PATH),
        "last_modified": last_modified,
        "summary": summary,
        "content": content,
    }


def _save_history_snapshot() -> None:
    """Copy current rsyslog.conf into HISTORY_DIR, prune oldest if > MAX_HISTORY."""
    if not CONFIG_PATH.exists():
        return
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(CONFIG_PATH, HISTORY_DIR / f"rsyslog.conf.{ts}")
    snapshots = sorted(HISTORY_DIR.glob("rsyslog.conf.*"))
    for old in snapshots[:-MAX_HISTORY]:
        old.unlink(missing_ok=True)


def write_config(content: str) -> None:
    if not CONFIG_PATH.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="rsyslog configuration file not found")

    _save_history_snapshot()
    shutil.copy2(CONFIG_PATH, CONFIG_BACKUP_PATH)
    CONFIG_PATH.write_text(content, encoding="utf-8")


def get_logs(lines: int, priority: Optional[str] = None) -> str:
    cmd = ["journalctl", "-u", LOG_SERVICE, "-n", str(lines), "--no-pager"]
    if priority:
        cmd.extend(["-p", priority])
    return run_command(cmd)


@router.get("/status")
async def get_rsyslog_status(current_user: dict = Depends(get_current_user)):
    status_data = get_service_status()
    # Extended systemd properties
    props = [
        "ActiveEnterTimestamp", "NRestarts", "ExecMainStatus",
        "ActiveState", "SubState", "MainPID",
    ]
    try:
        raw = subprocess.run(
            ["systemctl", "show", LOG_SERVICE, f"--property={','.join(props)}"],
            capture_output=True, text=True, timeout=5,
        ).stdout
        kv: Dict[str, str] = {}
        for line in raw.splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                kv[k.strip()] = v.strip()
        status_data["uptime"]       = kv.get("ActiveEnterTimestamp", "unknown")
        status_data["n_restarts"]   = int(kv.get("NRestarts", "0") or "0")
        status_data["main_pid"]     = kv.get("MainPID", "0")
        status_data["exec_status"]  = kv.get("ExecMainStatus", "0")
        status_data["sub_state"]    = kv.get("SubState", "unknown")
    except Exception:
        status_data["uptime"]      = "unknown"
        status_data["n_restarts"]  = -1
        status_data["main_pid"]    = "0"
        status_data["exec_status"] = "0"
        status_data["sub_state"]   = "unknown"
    return status_data


@router.get("/config")
async def get_rsyslog_config(current_user: dict = Depends(get_current_user)):
    config_data = get_config_summary()
    config_data["editable"] = current_user["role"] in [UserRole.admin, UserRole.operator]
    return config_data


@router.put("/config")
async def update_rsyslog_config(
    payload: RsyslogConfigUpdate,
    current_user: dict = Depends(require_role([UserRole.admin, UserRole.operator])),
):
    write_config(payload.content)
    log_action(current_user["username"], "config.update", str(CONFIG_PATH))
    return {
        "status": "success",
        "message": "rsyslog configuration updated and backed up.",
    }


@router.post("/config/check")
async def check_rsyslog_config(
    payload: RsyslogConfigUpdate,
    current_user: dict = Depends(require_role([UserRole.admin, UserRole.operator])),
):
    """Run rsyslogd -N1 against the supplied config content without writing it to disk."""
    import tempfile, os
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".conf", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(payload.content)
        tmp_path = tmp.name
    try:
        result = subprocess.run(
            ["rsyslogd", "-N1", "-f", tmp_path],
            capture_output=True, text=True, timeout=15,
        )
        # rsyslogd -N1 writes diagnostics to stderr, exit code 0 = OK
        output = (result.stderr + result.stdout).strip()
        ok = result.returncode == 0
        return {"ok": ok, "output": output, "returncode": result.returncode}
    except FileNotFoundError:
        return {"ok": None, "output": "rsyslogd nicht gefunden — Prüfung nur auf dem Zielsystem möglich.", "returncode": -1}
    except subprocess.TimeoutExpired:
        return {"ok": False, "output": "Timeout bei der Syntax-Prüfung.", "returncode": -1}
    finally:
        os.unlink(tmp_path)


@router.post("/reload", status_code=status.HTTP_200_OK)
async def reload_rsyslog_config(current_user: dict = Depends(require_role([UserRole.admin, UserRole.operator]))):
    run_command(["sudo", "-n", "systemctl", "reload", LOG_SERVICE])
    log_action(current_user["username"], "service.reload", LOG_SERVICE)
    return {"status": "success", "message": "rsyslog configuration reloaded successfully."}


@router.post("/restart", status_code=status.HTTP_200_OK)
async def restart_rsyslog(current_user: dict = Depends(require_role([UserRole.admin]))):
    run_command(["sudo", "-n", "systemctl", "restart", LOG_SERVICE])
    log_action(current_user["username"], "service.restart", LOG_SERVICE)
    return {"status": "success", "message": "rsyslog service restarted."}


@router.post("/stop", status_code=status.HTTP_200_OK)
async def stop_rsyslog(current_user: dict = Depends(require_role([UserRole.admin]))):
    run_command(["sudo", "-n", "systemctl", "stop", LOG_SERVICE])
    log_action(current_user["username"], "service.stop", LOG_SERVICE)
    return {"status": "success", "message": "rsyslog service stopped."}


@router.post("/start", status_code=status.HTTP_200_OK)
async def start_rsyslog(current_user: dict = Depends(require_role([UserRole.admin]))):
    run_command(["sudo", "-n", "systemctl", "start", LOG_SERVICE])
    log_action(current_user["username"], "service.start", LOG_SERVICE)
    return {"status": "success", "message": "rsyslog service started."}


@router.get("/config/history")
async def list_config_history(current_user: dict = Depends(get_current_user)):
    """List available config snapshots, newest first."""
    if not HISTORY_DIR.exists():
        return {"snapshots": []}
    snapshots = []
    for f in sorted(HISTORY_DIR.glob("rsyslog.conf.*"), reverse=True):
        ts_str = f.name.replace("rsyslog.conf.", "")
        try:
            ts = datetime.strptime(ts_str, "%Y%m%d_%H%M%S")
            label = ts.strftime("%d.%m.%Y %H:%M:%S")
        except ValueError:
            label = ts_str
        snapshots.append({
            "name": f.name,
            "label": label,
            "size": f.stat().st_size,
        })
    return {"snapshots": snapshots}


@router.get("/config/history/{snapshot_name}")
async def get_config_snapshot(
    snapshot_name: str,
    current_user: dict = Depends(get_current_user),
):
    if not re.match(r"^rsyslog\.conf\.\d{8}_\d{6}$", snapshot_name):
        raise HTTPException(status_code=400, detail="Ungültiger Snapshot-Name")
    path = HISTORY_DIR / snapshot_name
    if not path.exists():
        raise HTTPException(status_code=404, detail="Snapshot nicht gefunden")
    snap_content = path.read_text(encoding="utf-8", errors="replace")
    current_content = CONFIG_PATH.read_text(encoding="utf-8", errors="replace") if CONFIG_PATH.exists() else ""
    diff = list(difflib.unified_diff(
        current_content.splitlines(keepends=True),
        snap_content.splitlines(keepends=True),
        fromfile="aktuell",
        tofile=snapshot_name,
        lineterm="",
    ))
    return {
        "name": snapshot_name,
        "content": snap_content,
        "diff": "".join(diff),
        "diff_lines": len(diff),
    }


@router.post("/config/rollback")
async def rollback_config(
    payload: dict,
    current_user: dict = Depends(require_role([UserRole.admin])),
):
    snapshot_name = payload.get("snapshot", "")
    if not re.match(r"^rsyslog\.conf\.\d{8}_\d{6}$", snapshot_name):
        raise HTTPException(status_code=400, detail="Ungültiger Snapshot-Name")
    path = HISTORY_DIR / snapshot_name
    if not path.exists():
        raise HTTPException(status_code=404, detail="Snapshot nicht gefunden")
    content = path.read_text(encoding="utf-8", errors="replace")
    write_config(content)
    log_action(current_user["username"], "config.rollback", snapshot_name)
    return {"status": "success", "message": f"Konfiguration auf {snapshot_name} zurückgesetzt."}


@router.get("/config/download")
async def download_config(current_user: dict = Depends(get_current_user)):
    """Download current rsyslog.conf as file attachment."""
    if not CONFIG_PATH.exists():
        raise HTTPException(status_code=404, detail="Datei nicht gefunden")
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return FileResponse(
        path=str(CONFIG_PATH),
        media_type="text/plain",
        filename=f"rsyslog.conf.{ts}",
        headers={"Content-Disposition": f'attachment; filename="rsyslog.conf.{ts}"'},
    )


@router.post("/config/restore")
async def restore_config(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_role([UserRole.admin])),
):
    """Upload a rsyslog.conf to restore (replaces current config after creating snapshot)."""
    content = (await file.read()).decode("utf-8", errors="replace")
    if len(content) > 512_000:
        raise HTTPException(status_code=413, detail="Datei zu groß (max. 512 KB)")
    write_config(content)
    log_action(current_user["username"], "config.restore", file.filename or "upload")
    return {"status": "success", "message": "Konfiguration aus Upload wiederhergestellt."}


@router.get("/logs")
async def get_rsyslog_logs(
    lines: int = Query(100, ge=10, le=1000),
    priority: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    logs = get_logs(lines, priority)
    return {"logs": logs}


def _user_allowed_hosts(username: str) -> Optional[List[str]]:
    """Return allowed host list (group-aware), or None meaning unrestricted."""
    from .groups import get_user_effective_hosts
    return get_user_effective_hosts(username)


def _hostname_from_path(log_file: Path) -> str:
    """Extract hostname from log file path.

    Supports two layouts:
      host-based:     /data/syslog/HOSTNAME/YYYY/MM/HOSTNAME_[IP].log
      category-based: /data/syslog/CATEGORY/YYYY/MM/HOSTNAME_[IP].log
    The hostname is always encoded in the filename stem as HOSTNAME_[IP].
    """
    stem = log_file.stem  # e.g. "server01_[192.168.1.10]"
    return stem.split("_[")[0] if "_[" in stem else stem


def _parse_log_line(line: str, hostname_fallback: str) -> Dict:
    """Parse one log line: tries JSON first, then fixes unquoted message value."""
    entry = None
    try:
        entry = json.loads(line)
    except json.JSONDecodeError:
        fixed = _RE_FIX_MSG.sub(
            lambda m: m.group(1) + '"'
            + m.group(2).rstrip().replace("\\", "\\\\").replace('"', '\\"')
            + '"}',
            line,
        )
        if fixed != line:
            try:
                entry = json.loads(fixed)
            except json.JSONDecodeError:
                pass

    if entry is None:
        return {"raw": line, "hostname": hostname_fallback}

    # tag → programname (strip trailing colon, strip PID brackets)
    if "tag" in entry and "programname" not in entry:
        tag = str(entry["tag"]).rstrip(": ")
        entry["programname"] = re.sub(r"\[\d+\]$", "", tag)

    # string severity → numeric syslogseverity for badge styling
    if "severity" in entry and "syslogseverity" not in entry:
        sev = str(entry["severity"]).lower().strip()
        if sev in _SEV_MAP:
            entry["syslogseverity"] = _SEV_MAP[sev]

    return entry


def _read_remote_logs(
    allowed_hosts: Optional[List[str]],
    host_filter: Optional[str],
    limit: int,
) -> List[Dict]:
    """Read JSON log entries from /data/syslog/ (both host- and category-based layouts)."""
    if not SYSLOG_DATA_DIR.exists():
        return []

    log_files: List[Path] = []
    for log_file in sorted(SYSLOG_DATA_DIR.rglob("*.log"), reverse=True):
        hostname = _hostname_from_path(log_file)
        if allowed_hosts is not None and hostname not in allowed_hosts:
            continue
        if host_filter and hostname != host_filter:
            continue
        log_files.append(log_file)

    entries: List[Dict] = []
    for log_file in log_files:
        if len(entries) >= limit:
            break
        try:
            lines = log_file.read_text(encoding="utf-8", errors="replace").splitlines()
            for line in reversed(lines):
                if len(entries) >= limit:
                    break
                line = line.strip()
                if not line:
                    continue
                entries.append(_parse_log_line(line, _hostname_from_path(log_file)))
        except OSError:
            continue

    return entries[:limit]


@router.get("/remote-logs")
async def get_remote_logs(
    limit: int = Query(200, ge=10, le=2000),
    host: Optional[str] = Query(None, description="Filter by hostname"),
    current_user: dict = Depends(get_current_user),
):
    allowed = _user_allowed_hosts(current_user["username"])
    # Validate requested host against allowed hosts
    if host and allowed is not None and host not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access to host '{host}' not permitted for this user",
        )
    entries = _read_remote_logs(allowed, host, limit)
    return {"entries": entries, "count": len(entries), "allowed_hosts": allowed}


@router.get("/remote-logs/hosts")
async def get_available_hosts(current_user: dict = Depends(get_current_user)):
    """Return list of hosts visible to this user (from log files on disk)."""
    allowed = _user_allowed_hosts(current_user["username"])
    found: set[str] = set()
    if SYSLOG_DATA_DIR.exists():
        for log_file in SYSLOG_DATA_DIR.rglob("*.log"):
            hostname = _hostname_from_path(log_file)
            if allowed is None or hostname in allowed:
                found.add(hostname)
    return {"hosts": sorted(found)}


# ── Log-Datei-Explorer ────────────────────────────────────────────────────────

def _safe_log_path(rel_path: str, allowed_hosts: Optional[List[str]]) -> Path:
    """Resolve rel_path under SYSLOG_DATA_DIR and validate access. Raises HTTPException on error."""
    # Strict: no '..' components, no absolute paths (forward or back slash)
    if ".." in rel_path or rel_path.startswith("/") or rel_path.startswith("\\"):
        raise HTTPException(status_code=400, detail="Ungültiger Pfad")
    full = (SYSLOG_DATA_DIR / rel_path).resolve()
    # Must stay inside SYSLOG_DATA_DIR
    try:
        full.relative_to(SYSLOG_DATA_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Zugriff verweigert")
    # Extract hostname from first path component
    hostname = rel_path.split("/")[0]
    if allowed_hosts is not None and hostname not in allowed_hosts:
        raise HTTPException(status_code=403, detail=f"Kein Zugriff auf Host '{hostname}'")
    return full


@router.get("/files")
async def list_log_files(current_user: dict = Depends(get_current_user)):
    """Return hierarchical listing of log files grouped by host → year → month."""
    allowed = _user_allowed_hosts(current_user["username"])
    if not SYSLOG_DATA_DIR.exists():
        return {"tree": [], "total_files": 0, "total_bytes": 0}

    tree: Dict[str, Dict] = {}
    total_files = 0
    total_bytes = 0

    for f in sorted(SYSLOG_DATA_DIR.rglob("*.log*")):
        hostname = _hostname_from_path(f)
        if allowed is not None and hostname not in allowed:
            continue
        # relative path from SYSLOG_DATA_DIR
        rel = f.relative_to(SYSLOG_DATA_DIR)
        parts = rel.parts  # e.g. ("server01", "2026", "06", "server01_[10.0.0.1].log")
        host = parts[0]
        year = parts[1] if len(parts) > 2 else "—"
        month = parts[2] if len(parts) > 3 else "—"
        fname = parts[-1]
        stat = f.stat()
        total_files += 1
        total_bytes += stat.st_size

        tree.setdefault(host, {})
        tree[host].setdefault(year, {})
        tree[host][year].setdefault(month, [])
        tree[host][year][month].append({
            "name": fname,
            "path": str(rel).replace("\\", "/"),
            "size": stat.st_size,
            "modified": datetime.utcfromtimestamp(stat.st_mtime).isoformat() + "Z",
        })

    # Convert to list format for JSON serialisation
    result = []
    for host, years in sorted(tree.items()):
        host_entry = {"host": host, "years": []}
        for year, months in sorted(years.items(), reverse=True):
            year_entry = {"year": year, "months": []}
            for month, files in sorted(months.items(), reverse=True):
                year_entry["months"].append({
                    "month": month,
                    "files": sorted(files, key=lambda x: x["modified"], reverse=True),
                })
            host_entry["years"].append(year_entry)
        result.append(host_entry)

    return {"tree": result, "total_files": total_files, "total_bytes": total_bytes}


@router.get("/files/download")
async def download_log_file(
    path: str = Query(..., description="Relative path under /data/syslog"),
    current_user: dict = Depends(get_current_user),
):
    """Stream a single log file to the browser."""
    allowed = _user_allowed_hosts(current_user["username"])
    full_path = _safe_log_path(path, allowed)
    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="Datei nicht gefunden")

    filename = full_path.name
    media_type = "application/gzip" if filename.endswith(".gz") else "text/plain"
    return FileResponse(
        path=str(full_path),
        media_type=media_type,
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── /etc/rsyslog.d/ include files ────────────────────────────────────────────

RSYSLOG_D = Path("/etc/rsyslog.d")
# Allow .conf and .json (lookup tables) — no path separators, no ..
_SAFE_NAME = re.compile(r"^[\w\-\.]+\.(conf|json)$")


def _safe_include_path(filename: str) -> Path:
    if not _SAFE_NAME.match(filename):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Ungültiger Dateiname (nur *.conf oder *.json erlaubt)")
    return RSYSLOG_D / filename


@router.get("/includes")
async def list_includes(current_user: dict = Depends(get_current_user)):
    """List all .conf and .json files in /etc/rsyslog.d/."""
    if not RSYSLOG_D.exists():
        return {"files": []}
    files = []
    for f in sorted(list(RSYSLOG_D.glob("*.conf")) + list(RSYSLOG_D.glob("*.json"))):
        stat = f.stat()
        is_conf = f.suffix == ".conf"
        files.append({
            "name": f.name,
            "size": stat.st_size,
            "modified": datetime.utcfromtimestamp(stat.st_mtime).isoformat() + "Z",
            "managed": is_conf and f.read_text(encoding="utf-8", errors="replace").startswith(
                "# managed by rsyslog-manager"
            ) if stat.st_size < 4096 else False,
            "type": "json" if not is_conf else "conf",
        })
    return {"files": sorted(files, key=lambda x: x["name"])}


@router.get("/includes/{filename}")
async def get_include(
    filename: str,
    current_user: dict = Depends(get_current_user),
):
    path = _safe_include_path(filename)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Datei nicht gefunden")
    content = path.read_text(encoding="utf-8", errors="replace")
    stat = path.stat()
    return {
        "name": filename,
        "content": content,
        "size": stat.st_size,
        "modified": datetime.utcfromtimestamp(stat.st_mtime).isoformat() + "Z",
        "managed": content.startswith("# managed by rsyslog-manager"),
    }


@router.put("/includes/{filename}")
async def put_include(
    filename: str,
    payload: RsyslogConfigUpdate,
    current_user: dict = Depends(require_role([UserRole.admin, UserRole.operator])),
):
    path = _safe_include_path(filename)
    if path.exists():
        # Backup before overwrite
        shutil.copy2(path, path.with_suffix(".conf.bak"))
    RSYSLOG_D.mkdir(parents=True, exist_ok=True)
    path.write_text(payload.content, encoding="utf-8")
    log_action(current_user["username"], "include.update", filename)
    return {"status": "success", "message": f"{filename} gespeichert."}


@router.delete("/includes/{filename}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_include(
    filename: str,
    current_user: dict = Depends(require_role([UserRole.admin])),
):
    path = _safe_include_path(filename)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Datei nicht gefunden")
    content = path.read_text(encoding="utf-8", errors="replace")
    if content.startswith("# managed by rsyslog-manager"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Managed-Datei kann nicht manuell gelöscht werden. Deaktiviere die Funktion in den Einstellungen.",
        )
    path.unlink()
    log_action(current_user["username"], "include.delete", filename)


# ── Lookup-Tables ────────────────────────────────────────────────────────────

_SAFE_LOOKUP = re.compile(r"^lookup_[\w\-]+\.json$")


@router.get("/lookup-tables")
async def list_lookup_tables(current_user: dict = Depends(get_current_user)):
    """Return all lookup_*.json files from /etc/rsyslog.d/ with their entries."""
    tables: List[Dict] = []
    for f in sorted(RSYSLOG_D.glob("lookup_*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            tables.append({
                "filename": f.name,
                "name": f.stem.replace("lookup_", "RSYSLOG_TBL_"),
                "entries": data.get("table", []),
            })
        except Exception:
            pass
    return {"tables": tables}


@router.put("/lookup-tables/{filename}")
async def update_lookup_table(
    filename: str,
    entries: List[Dict],
    current_user: dict = Depends(require_role([UserRole.admin, UserRole.operator])),
):
    """Replace all entries in a lookup table and signal rsyslog to reload."""
    if not _SAFE_LOOKUP.match(filename):
        raise HTTPException(status_code=400, detail="Ungültiger Dateiname")
    path = RSYSLOG_D / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Lookup-Tabelle nicht gefunden")
    existing = json.loads(path.read_text(encoding="utf-8"))
    # Validate entries
    for e in entries:
        if "index" not in e or "value" not in e:
            raise HTTPException(status_code=422, detail="Einträge müssen 'index' und 'value' haben")
    existing["table"] = entries
    path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    # Reload rsyslog so it picks up the updated lookup table (reloadOnHUP="on")
    try:
        subprocess.run(["sudo", "-n", "systemctl", "reload", LOG_SERVICE],
                       capture_output=True, timeout=10)
    except Exception:
        pass
    log_action(current_user["username"], "lookup_table.update",
               f"{filename} ({len(entries)} Einträge)")
    return {"status": "success", "message": f"{filename} gespeichert."}


@router.post("/lookup-tables")
async def create_lookup_table(
    filename: str,
    current_user: dict = Depends(require_role([UserRole.admin])),
):
    """Create a new empty lookup table JSON file."""
    if not _SAFE_LOOKUP.match(filename):
        raise HTTPException(status_code=400, detail="Ungültiger Dateiname")
    path = RSYSLOG_D / filename
    if path.exists():
        raise HTTPException(status_code=409, detail="Datei existiert bereits")
    template = {"version": 1, "nomatch": "", "type": "string", "table": []}
    RSYSLOG_D.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(template, indent=2), encoding="utf-8")
    log_action(current_user["username"], "lookup_table.create", filename)
    return {"status": "success", "filename": filename}


# ── Heartbeat ────────────────────────────────────────────────────────────────

HEARTBEAT_WARN_S = 900    # 15 min
HEARTBEAT_CRIT_S = 3600   # 1 h


@router.get("/heartbeat")
async def get_heartbeat(current_user: dict = Depends(get_current_user)):
    allowed = _user_allowed_hosts(current_user["username"])
    if not SYSLOG_DATA_DIR.exists():
        return {"hosts": [], "warn_threshold": HEARTBEAT_WARN_S, "crit_threshold": HEARTBEAT_CRIT_S}

    now = time.time()
    result = []
    for host_dir in sorted(SYSLOG_DATA_DIR.iterdir()):
        if not host_dir.is_dir():
            continue
        host = host_dir.name
        if allowed is not None and host not in allowed:
            continue

        last_ts: Optional[float] = None
        for f in host_dir.rglob("*.log*"):
            try:
                mtime = f.stat().st_mtime
                if last_ts is None or mtime > last_ts:
                    last_ts = mtime
            except OSError:
                pass

        if last_ts is None:
            result.append({"host": host, "last_seen": None, "age_seconds": None, "status": "unknown"})
        else:
            age = int(now - last_ts)
            result.append({
                "host": host,
                "last_seen": datetime.utcfromtimestamp(last_ts).isoformat() + "Z",
                "age_seconds": age,
                "status": "ok" if age < HEARTBEAT_WARN_S else ("warn" if age < HEARTBEAT_CRIT_S else "crit"),
            })

    return {"hosts": result, "warn_threshold": HEARTBEAT_WARN_S, "crit_threshold": HEARTBEAT_CRIT_S}


# ── Event-rate + Anomalie-Erkennung ─────────────────────────────────────────

ANOMALY_ALERTS_JSON = Path("/etc/rsyslog-manager/anomaly_alerts.json")
ANOMALY_THROTTLE_S  = 3600   # min interval between anomaly emails per host
ANOMALY_FACTOR      = 3.0    # current hour > N× rolling average → anomaly


def _tail_lines(path: Path, n: int = 30000) -> List[str]:
    try:
        import gzip as _gzip
        if path.suffix == ".gz":
            with _gzip.open(path, "rt", errors="ignore") as fh:
                return list(fh)[-n:]
        content = path.read_text(errors="ignore")
        lines = content.splitlines()
        return lines[-n:]
    except Exception:
        return []


def _count_events_per_host(allowed: Optional[List[str]], days_back: int = 14
                            ) -> Dict[str, Dict[str, int]]:
    """
    Returns {host: {bucket_key: count}} where bucket_key is
    'h{0..23}' for hourly (last 24h) or 'd{0..days_back-1}' for daily.
    """
    if not SYSLOG_DATA_DIR.exists():
        return {}

    now = datetime.utcnow()
    cutoff = now - timedelta(days=days_back)
    result: Dict[str, Dict[str, int]] = {}

    for host_dir in sorted(SYSLOG_DATA_DIR.iterdir()):
        if not host_dir.is_dir():
            continue
        host = host_dir.name
        if allowed is not None and host not in allowed:
            continue

        hourly = {i: 0 for i in range(24)}
        daily  = {i: 0 for i in range(days_back)}

        for f in sorted(host_dir.rglob("*.log")):
            try:
                mtime = datetime.utcfromtimestamp(f.stat().st_mtime)
                if mtime < cutoff:
                    continue
            except OSError:
                continue

            for line in _tail_lines(f):
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    ts_raw = entry.get("timereported") or entry.get("timestamp", "")
                    ts = datetime.fromisoformat(ts_raw[:19])   # strip tz suffix
                    diff = now - ts
                    h = int(diff.total_seconds() / 3600)
                    d = int(diff.total_seconds() / 86400)
                    if 0 <= h < 24:
                        hourly[h] += 1
                    if 0 <= d < days_back:
                        daily[d] += 1
                except Exception:
                    pass

        result[host] = {"hourly": hourly, "daily": daily}

    return result


def _load_anomaly_times() -> Dict[str, str]:
    if ANOMALY_ALERTS_JSON.exists():
        try:
            return json.loads(ANOMALY_ALERTS_JSON.read_text())
        except Exception:
            pass
    return {}


def _save_anomaly_times(data: Dict[str, str]) -> None:
    ANOMALY_ALERTS_JSON.parent.mkdir(parents=True, exist_ok=True)
    ANOMALY_ALERTS_JSON.write_text(json.dumps(data, indent=2))


def _send_anomaly_email(host: str, current_count: int, avg_count: float,
                        recipients: List[str], smtp_cfg: dict) -> bool:
    if not recipients or not smtp_cfg.get("smtp_server"):
        return False
    body = (
        f"Anomalie erkannt auf Host: {host}\n\n"
        f"Events in der letzten Stunde: {current_count}\n"
        f"Durchschnitt (letzte 7 Tage):  {avg_count:.1f}\n"
        f"Faktor:                        {current_count / avg_count:.1f}×\n\n"
        f"Zeitpunkt: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
        f"-- RSYSLOG Manager"
    )
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = f"[RSYSLOG] Anomalie auf {host}: {current_count} Events/h"
    msg["From"]    = smtp_cfg.get("mail_from", "rsyslog-manager@localhost")
    msg["To"]      = ", ".join(recipients)
    try:
        with smtplib.SMTP(smtp_cfg["smtp_server"], int(smtp_cfg.get("smtp_port", 25)),
                          timeout=10) as s:
            s.sendmail(msg["From"], recipients, msg.as_string())
        return True
    except Exception:
        return False


@router.get("/event-rate")
async def get_event_rate(current_user: dict = Depends(get_current_user)):
    allowed = _user_allowed_hosts(current_user["username"])
    counts  = _count_events_per_host(allowed, days_back=14)

    hourly_out = []
    daily_out  = []
    anomalies  = []

    for host, data in counts.items():
        h_counts = [data["hourly"].get(i, 0) for i in range(24)]
        d_counts = [data["daily"].get(i, 0) for i in range(14)]
        hourly_out.append({"host": host, "counts": h_counts})
        daily_out.append({"host": host, "counts": d_counts})

        # Anomaly: last hour vs rolling 7-day hourly average
        current_h   = h_counts[0]
        rolling_avg = sum(h_counts[1:]) / max(len(h_counts) - 1, 1)
        if rolling_avg > 0 and current_h > ANOMALY_FACTOR * rolling_avg:
            anomalies.append({
                "host": host,
                "current_count": current_h,
                "rolling_avg": round(rolling_avg, 1),
                "factor": round(current_h / rolling_avg, 1),
            })

    # Send anomaly emails (throttled, maintenance-aware) — only for admin/operator
    if anomalies and (current_user.get("role") in ("admin", "operator")):
        from .settings import _read_email, is_maintenance_active
        from .groups import get_alert_recipients_for_host
        if not is_maintenance_active():
            smtp_cfg = _read_email().model_dump()
            if smtp_cfg.get("enabled"):
                alert_times = _load_anomaly_times()
                now_iso = datetime.utcnow().isoformat()
                changed = False
                for an in anomalies:
                    h = an["host"]
                    last = alert_times.get(h)
                    if last:
                        try:
                            elapsed = (datetime.utcnow() - datetime.fromisoformat(last)).total_seconds()
                            if elapsed < ANOMALY_THROTTLE_S:
                                continue
                        except Exception:
                            pass
                    recipients = get_alert_recipients_for_host(h)
                    if _send_anomaly_email(h, an["current_count"], an["rolling_avg"],
                                           recipients, smtp_cfg):
                        alert_times[h] = now_iso
                        changed = True
                        log_action(current_user["username"], "anomaly.alert",
                                   f"host={h} count={an['current_count']} avg={an['rolling_avg']:.1f}")
                if changed:
                    _save_anomaly_times(alert_times)

    return {
        "hourly": hourly_out,
        "daily":  daily_out,
        "anomalies": anomalies,
    }


# ── Receiver-Ports ───────────────────────────────────────────────────────────

def _parse_receiver_ports() -> List[Dict]:
    """
    Parse rsyslog.conf + all /etc/rsyslog.d/*.conf files to find configured
    UDP/TCP input modules and their ports.  Works without host network namespace.

    Handles both RainerScript style:
      module(load="imudp")  input(type="imudp" port="514")
    and legacy $-directive style:
      $ModLoad imudp  $UDPServerRun 514
    """
    conf_files: List[Path] = []
    if CONFIG_PATH.exists():
        conf_files.append(CONFIG_PATH)
    if RSYSLOG_D.exists():
        conf_files.extend(sorted(RSYSLOG_D.glob("*.conf")))

    loaded_modules: set = set()
    ports: List[Dict] = []

    # regex patterns
    re_module_load  = re.compile(r'module\s*\(\s*load\s*=\s*"(im\w+)"', re.IGNORECASE)
    re_input_block  = re.compile(r'input\s*\(\s*type\s*=\s*"(im\w+)"[^)]*port\s*=\s*"(\d+)"', re.IGNORECASE | re.DOTALL)
    re_legacy_load  = re.compile(r'^\s*\$ModLoad\s+(im\w+)', re.IGNORECASE | re.MULTILINE)
    re_udp_run      = re.compile(r'^\s*\$UDPServerRun\s+(\d+)', re.IGNORECASE | re.MULTILINE)
    re_tcp_run      = re.compile(r'^\s*\$InputTCPServerRun\s+(\d+)', re.IGNORECASE | re.MULTILINE)

    for cf in conf_files:
        try:
            text = cf.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        for m in re_module_load.finditer(text):
            loaded_modules.add(m.group(1).lower())
        for m in re_legacy_load.finditer(text):
            loaded_modules.add(m.group(1).lower())

        for m in re_input_block.finditer(text):
            mod  = m.group(1).lower()
            port = m.group(2)
            proto = "udp" if "udp" in mod else ("tcp" if "tcp" in mod else mod)
            ports.append({"proto": proto, "local": f"*:{port}", "port": port, "source": cf.name})

        for m in re_udp_run.finditer(text):
            ports.append({"proto": "udp", "local": f"*:{m.group(1)}", "port": m.group(1), "source": cf.name})
        for m in re_tcp_run.finditer(text):
            ports.append({"proto": "tcp", "local": f"*:{m.group(1)}", "port": m.group(1), "source": cf.name})

    # De-duplicate
    seen: set = set()
    unique: List[Dict] = []
    for p in ports:
        key = (p["proto"], p["port"])
        if key not in seen:
            seen.add(key)
            unique.append(p)

    return unique


@router.get("/receiver-ports")
async def get_receiver_ports(current_user: dict = Depends(get_current_user)):
    """Return configured UDP/TCP input ports parsed from rsyslog.conf + /etc/rsyslog.d/."""
    return {"ports": _parse_receiver_ports()}


# ── Log-Directories ──────────────────────────────────────────────────────────

@router.get("/log-dirs")
async def get_log_dirs(current_user: dict = Depends(get_current_user)):
    """Return /data/syslog/ subdirectories with size, ownership, and permissions."""
    import pwd
    import grp

    dirs: List[Dict] = []
    if not SYSLOG_DATA_DIR.exists():
        return {"base_dir": str(SYSLOG_DATA_DIR), "dirs": dirs}

    for d in sorted(SYSLOG_DATA_DIR.iterdir()):
        if not d.is_dir():
            continue
        try:
            size = sum(f.stat().st_size for f in d.rglob("*") if f.is_file())
            st = d.stat()
            mode_oct = oct(st.st_mode)[-3:]
            try:
                owner = pwd.getpwuid(st.st_uid).pw_name
            except Exception:
                owner = str(st.st_uid)
            try:
                group = grp.getgrgid(st.st_gid).gr_name
            except Exception:
                group = str(st.st_gid)
            perms_ok = (owner in ("syslog", "rsyslog-mgr")) and (mode_oct in ("755", "750"))
            dirs.append({
                "name": d.name,
                "path": str(d),
                "size_bytes": size,
                "mode": mode_oct,
                "owner": owner,
                "group": group,
                "perms_ok": perms_ok,
            })
        except Exception:
            dirs.append({
                "name": d.name,
                "path": str(d),
                "size_bytes": 0,
                "mode": "???",
                "owner": "?",
                "group": "?",
                "perms_ok": False,
            })

    return {"base_dir": str(SYSLOG_DATA_DIR), "dirs": dirs}


@router.post("/log-dirs/ensure")
async def ensure_log_dir(
    payload: dict,
    current_user: dict = Depends(require_role([UserRole.admin, UserRole.operator])),
):
    """Create /data/syslog/<host>/ if absent and set chown syslog:adm chmod 755.

    Uses /usr/local/bin/rsyslog-mklogdir (deployed by deploy script) via sudo so
    the rsyslog-mgr user doesn't need a blanket chown capability.
    """
    host = (payload.get("host") or "").strip()
    if not re.match(r"^[\w][\w\-\.]{0,62}$", host):
        raise HTTPException(status_code=400, detail="Ungültiger Hostname")

    existed = (SYSLOG_DATA_DIR / host).exists()
    result = subprocess.run(
        ["sudo", "-n", "/usr/local/bin/rsyslog-mklogdir", host],
        capture_output=True, text=True, timeout=10,
    )
    if result.returncode != 0:
        err = result.stderr.strip() or result.stdout.strip()
        raise HTTPException(status_code=500, detail=f"Verzeichnis anlegen fehlgeschlagen: {err}")

    log_action(current_user["username"], "log_dir.ensure", str(SYSLOG_DATA_DIR / host))
    action = "Berechtigungen korrigiert" if existed else "Verzeichnis erstellt"
    return {"status": "success", "path": str(SYSLOG_DATA_DIR / host), "message": f"{host}: {action}"}

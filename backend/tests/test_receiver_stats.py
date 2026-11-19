"""Tests for heartbeat, event counting, tail reading and line counting (run from ./backend: pytest)."""
import gzip
import inspect
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app import rsyslog, stats


@pytest.fixture()
def logdir(tmp_path, monkeypatch):
    monkeypatch.setattr(rsyslog, "SYSLOG_DATA_DIR", tmp_path)
    monkeypatch.setattr(stats, "SYSLOG_DATA_DIR", tmp_path)
    rsyslog._heartbeat_cache.clear()
    rsyslog._event_rate_cache.clear()
    stats._line_count_cache.clear()
    return tmp_path


def write(path: Path, lines, mtime=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if mtime is not None:
        os.utime(path, (mtime, mtime))
    return path


def test_hostname_is_lowercased():
    assert rsyslog._hostname_from_path(Path("x/2026/11/SERVER01_[10.0.0.1].log")) == "server01"
    assert rsyslog._hostname_from_path(Path("x/plain.log")) == "plain"


def test_heartbeat_supports_both_layouts_and_empty_group_folders(logdir):
    write(logdir / "others/2026/11/server01_[10.0.0.1].log", ["a"])           # category layout
    write(logdir / "HostB/2026/11/HOSTB_[10.0.0.2].log", ["a"])                # host layout, mixed case
    (logdir / "BigIP/NODE1").mkdir(parents=True)                                 # silent group folders
    (logdir / "BigIP/NODE2").mkdir(parents=True)
    (logdir / "newhost").mkdir()                                               # freshly created, no logs yet

    by_host = {h["host"]: h for h in rsyslog._compute_heartbeat(None)}
    assert set(by_host) == {"server01", "hostb", "bigip/node1", "bigip/node2", "newhost"}   # "others"/"BigIP" are no hosts
    assert by_host["server01"]["status"] == "ok" and by_host["hostb"]["status"] == "ok"
    assert by_host["bigip/node1"]["status"] == "unknown" and by_host["newhost"]["last_seen"] is None

    assert [h["host"] for h in rsyslog._compute_heartbeat(["server01"])] == ["server01"]


def test_heartbeat_thresholds(logdir):
    old = time.time() - 2 * 3600
    write(logdir / "h/2026/11/stale_[10.0.0.3].log", ["a"], mtime=old)
    assert rsyslog._compute_heartbeat(None)[0]["status"] == "crit"


def test_tail_lines_plain_and_gzip(logdir):
    p = write(logdir / "t.log", [f"line{i}" for i in range(10)])
    assert rsyslog._tail_lines(p, n=3) == ["line7\n", "line8\n", "line9\n"]
    gz = logdir / "t.log.gz"
    with gzip.open(gz, "wt") as fh:
        fh.write("".join(f"g{i}\n" for i in range(5)))
    assert [l.strip() for l in rsyslog._tail_lines(gz, n=2)] == ["g3", "g4"]
    assert rsyslog._tail_lines(logdir / "missing.log") == []


def test_event_counting_handles_invalid_json_and_timezone_offset(logdir):
    now = datetime.now(timezone.utc)
    local = now.astimezone(timezone(timedelta(hours=2))).isoformat(timespec="seconds")      # e.g. ...+02:00
    older = (now - timedelta(hours=5)).isoformat(timespec="seconds")
    write(logdir / "others/2026/11/server01_[10.0.0.1].log", [
        '{"timereported":"%s","message":"valid json"}' % local,
        '{"timereported":"%s","message": unquoted text, not json}' % local,      # json.loads would drop this
        '{"timereported":"%s","message":"five hours ago"}' % older,
        "no timestamp at all",
    ])
    counts = rsyslog._count_events_per_host(None)
    hourly = counts["server01"]["hourly"]
    assert hourly[0] == 2 and hourly[5] == 1                # offset respected: +02:00 local == now (UTC)
    assert counts["server01"]["daily"][0] == 3


def test_event_counting_respects_allowed_hosts_case_insensitively(logdir):
    write(logdir / "x/2026/11/HostA_[10.0.0.1].log", ['{"timereported":"%s"}' % datetime.now(timezone.utc).isoformat()])
    write(logdir / "x/2026/11/hostb_[10.0.0.2].log", ['{"timereported":"%s"}' % datetime.now(timezone.utc).isoformat()])
    assert set(rsyslog._count_events_per_host(["hosta"])) == {"hosta"}


def test_line_counter_reads_only_appended_bytes_and_handles_rotation(logdir):
    p = write(logdir / "h/a_[10.0.0.1].log", ["1", "2", "3"])
    assert stats._count_log_lines() == 3
    with p.open("a") as fh:
        fh.write("4\n5\n")
    assert stats._count_log_lines() == 5                    # +2 appended lines, not a full re-read
    p.write_text("x\n")                                     # rotated / truncated
    assert stats._count_log_lines() == 1
    old = time.time() - 2 * 3600
    os.utime(p, (old, old))
    assert stats._count_log_lines() == 0                    # files not touched for an hour are skipped


def test_blocking_handlers_are_sync_but_upload_stays_async():
    assert not inspect.iscoroutinefunction(rsyslog.get_heartbeat)
    assert not inspect.iscoroutinefunction(rsyslog.get_event_rate)
    assert not inspect.iscoroutinefunction(stats.get_stats)
    src = inspect.getsource(rsyslog)
    assert "await file.read()" in src                       # the upload handler really needs async
    for name, fn in inspect.getmembers(rsyslog, inspect.iscoroutinefunction):
        assert "await" in inspect.getsource(fn), f"{name} is async without awaiting anything"


def test_routes_work_via_test_client(logdir):
    from fastapi.testclient import TestClient
    from app.deps import get_current_user
    from app.main import app

    write(logdir / "others/2026/11/server01_[10.0.0.1].log", ['{"timereported":"%s"}' % datetime.now(timezone.utc).isoformat()])
    app.dependency_overrides[get_current_user] = lambda: {"username": "admin", "role": "admin"}
    try:
        with TestClient(app) as client:                      # runs startup (thread limiter)
            r = client.get("/rsyslog/heartbeat")
            assert r.status_code == 200
            assert r.json()["unrestricted"] is True and [h["host"] for h in r.json()["hosts"]] == ["server01"]
            assert client.get("/rsyslog/event-rate").status_code == 200
    finally:
        app.dependency_overrides.clear()

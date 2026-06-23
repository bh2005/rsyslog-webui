"""In-memory ring buffer for backend log entries — feeds /api/syslogs."""

import collections
import logging
import threading
from datetime import datetime, timezone

_MAX_ENTRIES = 2000
_lock = threading.Lock()
_buffer: collections.deque = collections.deque(maxlen=_MAX_ENTRIES)
_installed = False


class RingBufferHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            ts = (
                datetime.fromtimestamp(record.created, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.")
                + f"{int(record.msecs):03d}Z"
            )
            entry: dict = {
                "ts": ts,
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }
            if record.exc_info:
                entry["exc"] = logging.Formatter().formatException(record.exc_info)
            with _lock:
                _buffer.append(entry)
        except Exception:
            pass


def install() -> None:
    global _installed
    if _installed:
        return
    h = RingBufferHandler(logging.DEBUG)
    logging.getLogger().addHandler(h)
    _installed = True


def get_entries(level: str | None = None, limit: int = 500) -> list[dict]:
    with _lock:
        entries = list(_buffer)
    if level and level.upper() not in ("ALL", ""):
        entries = [e for e in entries if e["level"] == level.upper()]
    return entries[-limit:]

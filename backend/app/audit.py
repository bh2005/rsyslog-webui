import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, Query

from .deps import get_current_user, require_role
from .models import UserRole

router = APIRouter(prefix="/audit", tags=["audit"])

AUDIT_LOG = Path("/etc/rsyslog-manager/audit.log")
_MAX_STORED = 10_000


def log_action(username: str, action: str, detail: str = "") -> None:
    """Append one audit entry (non-blocking, swallows write errors)."""
    try:
        AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "user": username,
            "action": action,
            "detail": detail,
        }
        with AUDIT_LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def read_audit(limit: int = 500) -> list[dict]:
    if not AUDIT_LOG.exists():
        return []
    lines = AUDIT_LOG.read_text(encoding="utf-8", errors="replace").splitlines()
    entries: list[dict] = []
    for line in reversed(lines[-_MAX_STORED:]):
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            pass
        if len(entries) >= limit:
            break
    return entries


@router.get("")
async def get_audit_log(
    limit: int = Query(200, ge=10, le=2000),
    _: dict = Depends(require_role([UserRole.admin])),
):
    return {"entries": read_audit(limit), "total": limit}


@router.delete("", status_code=204)
async def clear_audit_log(_: dict = Depends(require_role([UserRole.admin]))):
    """Truncate the audit log (irreversible)."""
    if AUDIT_LOG.exists():
        AUDIT_LOG.write_text("")

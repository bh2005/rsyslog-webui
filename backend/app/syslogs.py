"""System-Log-Viewer — In-Memory-Ringpuffer der Backend-Anwendungslogs."""

from fastapi import APIRouter, Depends, Query

from .deps import require_role
from .log_buffer import get_entries
from .models import UserRole

router = APIRouter(prefix="/syslogs", tags=["syslogs"])

_VALID_LEVELS = {"ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


@router.get("")
async def list_syslogs(
    level: str = Query("ALL"),
    limit: int = Query(500, ge=1, le=2000),
    _: dict = Depends(require_role([UserRole.admin])),
):
    lvl = level.upper() if level.upper() in _VALID_LEVELS else "ALL"
    return get_entries(level=lvl, limit=limit)

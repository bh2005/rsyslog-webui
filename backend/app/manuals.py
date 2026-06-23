import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import HTMLResponse

from .audit import log_action
from .deps import get_current_user, require_role
from .models import UserRole

router = APIRouter(prefix="/manuals", tags=["manuals"])

SETTINGS_DIR = Path("/etc/rsyslog-manager")
DOCS_DIR     = SETTINGS_DIR / "docs"      # built-in, read-only
MANUALS_DIR  = SETTINGS_DIR / "manuals"   # user uploads, read-write

_SAFE_NAME = re.compile(r"^[\w\- .]+\.html?$", re.IGNORECASE)
MAX_UPLOAD_BYTES = 2 * 1024 * 1024  # 2 MB


def _ensure_dirs() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    MANUALS_DIR.mkdir(parents=True, exist_ok=True)


def _list_files() -> list[dict]:
    _ensure_dirs()
    files: list[dict] = []

    for f in sorted(DOCS_DIR.glob("*.html")) + sorted(DOCS_DIR.glob("*.htm")):
        stat = f.stat()
        files.append({
            "name":     f.name,
            "category": "Dokumentation",
            "size":     stat.st_size,
            "readonly": True,
        })
    for f in sorted(MANUALS_DIR.glob("*.html")) + sorted(MANUALS_DIR.glob("*.htm")):
        stat = f.stat()
        files.append({
            "name":     f.name,
            "category": "Eigene Handbücher",
            "size":     stat.st_size,
            "readonly": False,
        })
    return files


def _resolve(name: str) -> tuple[Path, bool]:
    """Returns (path, is_readonly). Raises 404/400 if invalid."""
    if not _SAFE_NAME.match(name):
        raise HTTPException(status_code=400, detail="Ungültiger Dateiname")
    docs_path    = DOCS_DIR    / name
    manuals_path = MANUALS_DIR / name
    if docs_path.exists():
        return docs_path, True
    if manuals_path.exists():
        return manuals_path, False
    raise HTTPException(status_code=404, detail="Datei nicht gefunden")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("")
async def list_manuals(_: dict = Depends(get_current_user)):
    return {"files": _list_files()}


@router.get("/{name}/content", response_class=HTMLResponse)
async def get_manual_content(name: str, _: dict = Depends(get_current_user)):
    path, _ = _resolve(name)
    return HTMLResponse(content=path.read_text(encoding="utf-8", errors="replace"))


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_manual(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_role([UserRole.admin])),
):
    name = file.filename or "upload.html"
    if not _SAFE_NAME.match(name):
        raise HTTPException(status_code=400, detail="Ungültiger Dateiname (nur .html/.htm erlaubt)")
    MANUALS_DIR.mkdir(parents=True, exist_ok=True)

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"Datei zu groß (max. {MAX_UPLOAD_BYTES // 1024} KB)")

    dest = MANUALS_DIR / name
    dest.write_bytes(content)
    log_action(current_user["username"], "manuals.upload", name)
    return {"status": "success", "name": name, "size": len(content)}


@router.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_manual(
    name: str,
    current_user: dict = Depends(require_role([UserRole.admin])),
):
    path, readonly = _resolve(name)
    if readonly:
        raise HTTPException(status_code=409, detail="Eingebaute Dokumentation kann nicht gelöscht werden.")
    path.unlink()
    log_action(current_user["username"], "manuals.delete", name)

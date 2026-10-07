"""Gespeicherte Filter der Log-Analyse (pro Benutzer, max. MAX_FILTERS_PER_USER).

Jeder eingeloggte Benutzer kann den aktuellen Filter der Log-Analyse unter einem Namen
speichern und später wieder laden. Gespeichert wird serverseitig in
/etc/rsyslog-manager/saved_filters.json (je Benutzername eine Liste), damit die Filter
in jedem Browser und auf jedem Gerät verfügbar sind. Jeder sieht und ändert nur seine eigenen.
"""
import json
import os
import re
import threading
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from .deps import get_current_user

router = APIRouter(prefix="/users/me/filters", tags=["saved-filters"])

SETTINGS_DIR = Path("/etc/rsyslog-manager")
FILTERS_JSON = SETTINGS_DIR / "saved_filters.json"

MAX_FILTERS_PER_USER = 5
MAX_NAME_LEN = 40

_lock = threading.Lock()

_SEVERITIES = {str(i) for i in range(8)}
_FACILITIES = {
    "kern", "user", "mail", "daemon", "auth", "syslog", "lpr", "news", "cron",
    "local0", "local1", "local2", "local3", "local4", "local5", "local6", "local7",
}
_TIME_PRESETS = {"", "1h", "6h", "24h", "7d", "custom"}
_RE_LOCAL_DT = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?$")  # <input type="datetime-local">


class FilterSpec(BaseModel):
    """Zustand der Filterleiste der Log-Analyse."""
    host: str = Field("", max_length=253)
    severity: List[str] = Field(default_factory=list, max_length=8)
    facility: List[str] = Field(default_factory=list, max_length=17)
    program: str = Field("", max_length=100)
    q: str = Field("", max_length=200)
    regex: bool = False
    time_preset: str = ""
    time_from: str = Field("", max_length=32)
    time_to: str = Field("", max_length=32)
    limit: int = Field(500, ge=10, le=2000)

    @field_validator("severity")
    @classmethod
    def _check_severity(cls, v: List[str]) -> List[str]:
        if any(x not in _SEVERITIES for x in v):
            raise ValueError("Ungültiger Schweregrad")
        return v

    @field_validator("facility")
    @classmethod
    def _check_facility(cls, v: List[str]) -> List[str]:
        if any(x not in _FACILITIES for x in v):
            raise ValueError("Ungültige Facility")
        return v

    @field_validator("time_preset")
    @classmethod
    def _check_preset(cls, v: str) -> str:
        if v not in _TIME_PRESETS:
            raise ValueError("Ungültiger Zeitraum")
        return v

    @field_validator("time_from", "time_to")
    @classmethod
    def _check_local_dt(cls, v: str) -> str:
        if v and not _RE_LOCAL_DT.match(v):
            raise ValueError("Ungültiges Datum")
        return v


class SavedFilterIn(BaseModel):
    name: str
    filter: FilterSpec


class SavedFilterUpdate(BaseModel):
    """Teil-Update: neuer Name und/oder neue Filtereinstellungen (nicht gesetzte Felder bleiben)."""
    name: Optional[str] = None
    filter: Optional[FilterSpec] = None


class SavedFilter(BaseModel):
    id: str
    name: str
    filter: FilterSpec


def _load_all() -> Dict[str, List[dict]]:
    if FILTERS_JSON.exists():
        try:
            data = json.loads(FILTERS_JSON.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return {}


def _save_all(data: Dict[str, List[dict]]) -> None:
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    tmp = FILTERS_JSON.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.chmod(0o600)  # enthält Filter aller Benutzer: nur der Service-User soll lesen
    os.replace(tmp, FILTERS_JSON)  # atomar: ein Absturz mitten im Schreiben lässt keine halbe Datei zurück


def _user_filters(data: Dict[str, List[dict]], username: str) -> List[SavedFilter]:
    out: List[SavedFilter] = []
    for raw in data.get(username, []):
        try:
            out.append(SavedFilter(**raw))
        except Exception:
            continue  # defekten/veralteten Eintrag überspringen statt die ganze Liste zu verlieren
    return out


def _clean_name(raw: str) -> str:
    name = " ".join(raw.split())
    if not name or len(name) > MAX_NAME_LEN:
        raise HTTPException(status_code=400, detail=f"Der Name muss 1–{MAX_NAME_LEN} Zeichen lang sein")
    if any(not ch.isprintable() for ch in name):
        raise HTTPException(status_code=400, detail="Der Name enthält ungültige Zeichen")
    return name


def _response(filters: List[SavedFilter]) -> dict:
    return {"filters": [f.model_dump() for f in filters], "max": MAX_FILTERS_PER_USER}


@router.get("")
def list_filters(current_user: dict = Depends(get_current_user)):
    with _lock:
        return _response(_user_filters(_load_all(), current_user["username"]))


@router.put("")
def save_filter(body: SavedFilterIn, current_user: dict = Depends(get_current_user)):
    """Speichert den Filter unter `name`. Existiert der Name schon (Groß-/Kleinschreibung egal),
    wird er überschrieben; sonst wird ein neuer angelegt (max. MAX_FILTERS_PER_USER)."""
    name = _clean_name(body.name)
    username = current_user["username"]

    with _lock:
        data = _load_all()
        filters = _user_filters(data, username)
        existing = next((f for f in filters if f.name.casefold() == name.casefold()), None)
        if existing is not None:
            existing.name = name
            existing.filter = body.filter
        else:
            if len(filters) >= MAX_FILTERS_PER_USER:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Maximal {MAX_FILTERS_PER_USER} Filter möglich. Bitte zuerst einen löschen oder einen vorhandenen Namen überschreiben.",
                )
            filters.append(SavedFilter(id=uuid.uuid4().hex[:12], name=name, filter=body.filter))
        data[username] = [f.model_dump() for f in filters]
        _save_all(data)
        return _response(filters)


@router.patch("/{filter_id}")
def update_filter(filter_id: str, body: SavedFilterUpdate, current_user: dict = Depends(get_current_user)):
    """Ändert einen gespeicherten Filter: umbenennen und/oder mit neuen Einstellungen überschreiben."""
    if body.name is None and body.filter is None:
        raise HTTPException(status_code=400, detail="Nichts zu ändern")
    username = current_user["username"]
    with _lock:
        data = _load_all()
        filters = _user_filters(data, username)
        target = next((f for f in filters if f.id == filter_id), None)
        if target is None:
            raise HTTPException(status_code=404, detail="Filter nicht gefunden")
        if body.name is not None:
            name = _clean_name(body.name)
            if any(f.id != filter_id and f.name.casefold() == name.casefold() for f in filters):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Dieser Name ist bereits vergeben")
            target.name = name
        if body.filter is not None:
            target.filter = body.filter
        data[username] = [f.model_dump() for f in filters]
        _save_all(data)
        return _response(filters)


@router.delete("/{filter_id}")
def delete_filter(filter_id: str, current_user: dict = Depends(get_current_user)):
    username = current_user["username"]
    with _lock:
        data = _load_all()
        filters = _user_filters(data, username)
        remaining = [f for f in filters if f.id != filter_id]
        if len(remaining) == len(filters):
            raise HTTPException(status_code=404, detail="Filter nicht gefunden")
        data[username] = [f.model_dump() for f in remaining]
        _save_all(data)
        return _response(remaining)

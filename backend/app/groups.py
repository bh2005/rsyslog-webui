import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status

from .audit import log_action
from .deps import get_current_user, require_role
from .models import UserRole, fake_users_db
from .schemas import Group, GroupCreate, GroupUpdate

router = APIRouter(prefix="/groups", tags=["groups"])

SETTINGS_DIR = Path("/etc/rsyslog-manager")
GROUPS_JSON  = SETTINGS_DIR / "groups.json"


# ── Storage helpers ───────────────────────────────────────────────────────────

def _load_groups() -> dict[str, Group]:
    if GROUPS_JSON.exists():
        try:
            return {k: Group(**v) for k, v in json.loads(GROUPS_JSON.read_text()).items()}
        except Exception:
            pass
    return {}


def _save_groups(groups: dict[str, Group]) -> None:
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    GROUPS_JSON.write_text(json.dumps({k: v.model_dump() for k, v in groups.items()}, indent=2))


# ── Public helpers used by other modules ─────────────────────────────────────

def get_user_effective_hosts(username: str) -> list[str] | None:
    """None = unrestricted, list = restricted to these hosts."""
    u = fake_users_db.get(username)
    if not u:
        return []
    # Admins always have full access regardless of host/group settings
    if u.get("role") == UserRole.admin:
        return None
    user_hosts: list[str] = list(u.get("hosts", []))
    groups = _load_groups()

    if not user_hosts:
        # No direct restriction → check group membership
        group_hosts: list[str] = []
        for g in groups.values():
            if username in g.members:
                group_hosts.extend(g.hosts)
        if not group_hosts:
            return None   # unrestricted
        return list(set(group_hosts))

    # Has direct restriction → add group hosts on top
    for g in groups.values():
        if username in g.members:
            user_hosts.extend(g.hosts)
    return list(set(user_hosts))


def get_alert_recipients_for_host(host: str) -> list[str]:
    """Returns email addresses that should receive alerts for this host."""
    emails: set[str] = set()
    groups = _load_groups()

    for u in fake_users_db.values():
        email = u.get("email", "").strip()
        if not email:
            continue

        effective = get_user_effective_hosts(u["username"])
        if effective is None or host in effective:
            emails.add(email)

    return list(emails)


def collect_email_recipients() -> list[tuple[str, list[str]]]:
    """For email conf generation: [(email, effective_hosts)] — empty hosts = unrestricted."""
    groups = _load_groups()
    result: list[tuple[str, list[str]]] = []

    for u in fake_users_db.values():
        email = u.get("email", "").strip()
        if not email:
            continue
        effective = get_user_effective_hosts(u["username"])
        result.append((email, effective if effective is not None else []))

    return result


# ── CRUD endpoints ────────────────────────────────────────────────────────────

@router.get("", response_model=list[Group])
async def list_groups(_: dict = Depends(require_role([UserRole.admin]))):
    return list(_load_groups().values())


@router.post("", response_model=Group, status_code=status.HTTP_201_CREATED)
async def create_group(
    data: GroupCreate,
    current_user: dict = Depends(require_role([UserRole.admin])),
):
    groups = _load_groups()
    if data.name in groups:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"Gruppe '{data.name}' existiert bereits.")
    g = Group(**data.model_dump())
    groups[data.name] = g
    _save_groups(groups)
    log_action(current_user["username"], "group.create", data.name)
    return g


@router.put("/{name}", response_model=Group)
async def update_group(
    name: str,
    data: GroupUpdate,
    current_user: dict = Depends(require_role([UserRole.admin])),
):
    groups = _load_groups()
    if name not in groups:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gruppe nicht gefunden.")
    g = groups[name]
    if data.display_name is not None:
        g.display_name = data.display_name
    if data.members is not None:
        g.members = data.members
    if data.hosts is not None:
        g.hosts = data.hosts
    groups[name] = g
    _save_groups(groups)
    log_action(current_user["username"], "group.update",
               f"name={name} members={len(g.members)} hosts={len(g.hosts)}")
    return g


@router.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    name: str,
    current_user: dict = Depends(require_role([UserRole.admin])),
):
    groups = _load_groups()
    if name not in groups:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gruppe nicht gefunden.")
    del groups[name]
    _save_groups(groups)
    log_action(current_user["username"], "group.delete", name)

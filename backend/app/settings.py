import json
import re
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status

from .audit import log_action
from .deps import get_current_user, require_role
from .models import UserRole, fake_users_db
from .schemas import (EmailSettings, ForwardingSettings, Host,
                      MaintenanceSettings, MaintenanceWindow, RotationSettings)

router = APIRouter(prefix="/settings", tags=["settings"])

FORWARDING_CONF  = Path("/etc/rsyslog.d/99-forwarding.conf")
EMAIL_CONF       = Path("/etc/rsyslog.d/99-email-alerts.conf")
SETTINGS_DIR     = Path("/etc/rsyslog-manager")
EMAIL_JSON       = SETTINGS_DIR / "email_settings.json"
HOSTS_JSON       = SETTINGS_DIR / "hosts.json"
ROTATION_JSON    = SETTINGS_DIR / "rotation_settings.json"
MAINTENANCE_JSON = SETTINGS_DIR / "maintenance.json"
LOGROTATE_CONF   = Path("/etc/logrotate.d/rsyslog-remote")

MANAGED_MARKER  = "# managed by rsyslog-manager — do not edit manually"

SEVERITY_LABELS = {0: "emerg", 1: "alert", 2: "crit", 3: "err",
                   4: "warning", 5: "notice", 6: "info", 7: "debug"}


# ── Hosts ────────────────────────────────────────────────────────────────────

def _load_hosts() -> list[Host]:
    if HOSTS_JSON.exists():
        try:
            return [Host(**h) for h in json.loads(HOSTS_JSON.read_text())]
        except Exception:
            pass
    return []


def _save_hosts(hosts: list[Host]) -> None:
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    HOSTS_JSON.write_text(json.dumps([h.model_dump() for h in hosts], indent=2))


@router.get("/hosts", response_model=list[Host])
async def get_hosts(current_user: dict = Depends(get_current_user)):
    return _load_hosts()


@router.post("/hosts", response_model=Host, status_code=status.HTTP_201_CREATED)
async def add_host(
    host: Host,
    current_user: dict = Depends(require_role([UserRole.admin])),
):
    hosts = _load_hosts()
    if any(h.name == host.name for h in hosts):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"Host '{host.name}' already exists")
    hosts.append(host)
    _save_hosts(hosts)
    log_action(current_user["username"], "settings.host.add", host.name)
    return host


@router.put("/hosts/{name}", response_model=Host)
async def update_host(
    name: str,
    host: Host,
    _: dict = Depends(require_role([UserRole.admin])),
):
    hosts = _load_hosts()
    for i, h in enumerate(hosts):
        if h.name == name:
            hosts[i] = host
            _save_hosts(hosts)
            return host
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Host not found")


@router.delete("/hosts/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_host(
    name: str,
    current_user: dict = Depends(require_role([UserRole.admin])),
):
    hosts = _load_hosts()
    new_hosts = [h for h in hosts if h.name != name]
    if len(new_hosts) == len(hosts):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Host not found")
    _save_hosts(new_hosts)
    log_action(current_user["username"], "settings.host.delete", name)


# ── Forwarding ───────────────────────────────────────────────────────────────

def _read_forwarding() -> ForwardingSettings:
    if FORWARDING_CONF.exists():
        for line in FORWARDING_CONF.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            m = re.match(r"^\*\.\*\s+(@@|@)([^:]+):(\d+)", line)
            if m:
                return ForwardingSettings(
                    enabled=True,
                    protocol="tcp" if m.group(1) == "@@" else "udp",
                    host=m.group(2),
                    port=int(m.group(3)),
                )
    return ForwardingSettings()


def _write_forwarding(cfg: ForwardingSettings) -> None:
    if not cfg.enabled or not cfg.host:
        FORWARDING_CONF.unlink(missing_ok=True)
        return
    FORWARDING_CONF.parent.mkdir(parents=True, exist_ok=True)
    proto = "@@" if cfg.protocol == "tcp" else "@"
    FORWARDING_CONF.write_text(
        f"{MANAGED_MARKER}\n*.* {proto}{cfg.host}:{cfg.port}\n"
    )


@router.get("/forwarding", response_model=ForwardingSettings)
async def get_forwarding(current_user: dict = Depends(get_current_user)):
    return _read_forwarding()


@router.put("/forwarding")
async def put_forwarding(
    cfg: ForwardingSettings,
    current_user: dict = Depends(require_role([UserRole.admin, UserRole.operator])),
):
    try:
        _write_forwarding(cfg)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
    log_action(current_user["username"], "settings.forwarding",
               f"enabled={cfg.enabled} {cfg.protocol}://{cfg.host}:{cfg.port}")
    return {"status": "success", "message": "Forwarding-Einstellung gespeichert."}


# ── Email alerts ─────────────────────────────────────────────────────────────

def _read_email() -> EmailSettings:
    if EMAIL_JSON.exists():
        try:
            return EmailSettings(**json.loads(EMAIL_JSON.read_text()))
        except Exception:
            pass
    return EmailSettings()


def _write_email(cfg: EmailSettings) -> None:
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    EMAIL_JSON.write_text(json.dumps(cfg.model_dump(), indent=2))

    # Collect recipients using group-aware helper
    from .groups import collect_email_recipients
    alert_users = collect_email_recipients()  # [(email, effective_hosts)]

    if not cfg.enabled or not cfg.smtp_server or not alert_users:
        EMAIL_CONF.unlink(missing_ok=True)
        return

    EMAIL_CONF.parent.mkdir(parents=True, exist_ok=True)

    rules: list[str] = []
    for email_addr, hosts in alert_users:
        if hosts:
            host_cond = " or ".join(f'$hostname == "{h}"' for h in hosts)
            condition = f"({host_cond}) and $syslogseverity <= {cfg.min_severity}"
            comment = f"# {email_addr} → {', '.join(hosts)}"
        else:
            condition = f"$syslogseverity <= {cfg.min_severity}"
            comment = f"# {email_addr} → alle Hosts"

        rules.append(
            f"{comment}\n"
            f"if {condition} then\n"
            f"  action(type=\"ommail\"\n"
            f"         server=\"{cfg.smtp_server}\"\n"
            f"         port=\"{cfg.smtp_port}\"\n"
            f"         mailfrom=\"{cfg.mail_from}\"\n"
            f"         mailto=\"{email_addr}\"\n"
            f"         subject.text=\"rsyslog Alert [%syslogseverity-text%]: %hostname%\"\n"
            f"         action.execOnlyOnceEveryInterval=\"{cfg.throttle_interval}\"\n"
            f"         template=\"T_MANAGER_ALERT_BODY\")"
        )

    EMAIL_CONF.write_text(
        f"{MANAGED_MARKER}\n\n"
        f"module(load=\"ommail\")\n\n"
        f"template(name=\"T_MANAGER_ALERT_BODY\" type=\"string\"\n"
        f"  string=\"Alert from %hostname% (%fromhost-ip%)\\n"
        f"Severity:  %syslogseverity-text%\\n"
        f"Program:   %programname%\\n"
        f"Message:   %msg%\\n\")\n\n"
        + "\n\n".join(rules) + "\n"
    )


@router.get("/email", response_model=EmailSettings)
async def get_email(current_user: dict = Depends(get_current_user)):
    return _read_email()


@router.put("/email")
async def put_email(
    cfg: EmailSettings,
    current_user: dict = Depends(require_role([UserRole.admin, UserRole.operator])),
):
    try:
        _write_email(cfg)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
    log_action(current_user["username"], "settings.email",
               f"enabled={cfg.enabled} smtp={cfg.smtp_server}:{cfg.smtp_port} min_sev={cfg.min_severity}")
    return {"status": "success", "message": "E-Mail-Alert-Einstellung gespeichert."}


@router.post("/email/regenerate")
async def regenerate_email(current_user: dict = Depends(require_role([UserRole.admin]))):
    """Re-generate the email conf after user assignments changed."""
    cfg = _read_email()
    try:
        _write_email(cfg)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
    log_action(current_user["username"], "settings.email.regenerate", "")
    return {"status": "success", "message": "E-Mail-Konfiguration neu generiert."}


# ── Rotation / Archivierung ──────────────────────────────────────────────────

def _read_rotation() -> RotationSettings:
    if ROTATION_JSON.exists():
        try:
            return RotationSettings(**json.loads(ROTATION_JSON.read_text()))
        except Exception:
            pass
    return RotationSettings()


def _write_rotation(cfg: RotationSettings) -> None:
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    ROTATION_JSON.write_text(json.dumps(cfg.model_dump(), indent=2))

    if not cfg.enabled:
        LOGROTATE_CONF.unlink(missing_ok=True)
        return

    base = cfg.log_base_dir.rstrip("/")
    size_line = f"    size {cfg.max_size_mb}M\n" if cfg.max_size_mb > 0 else ""
    dateext_line = "    dateext\n    dateformat -%Y%m%d\n" if cfg.date_ext else ""
    compress_lines = "    compress\n    delaycompress\n" if cfg.compress else ""

    content = (
        f"# managed by rsyslog-manager — do not edit manually\n"
        f"{base}/*/*/*/*.log {base}/*/*/*.log {base}/*/*/*.log {base}/*/*.log {{\n"
        f"    {cfg.rotate_interval}\n"
        f"    rotate {cfg.rotate_count}\n"
        f"    missingok\n"
        f"    notifempty\n"
        f"    sharedscripts\n"
        f"{size_line}"
        f"{dateext_line}"
        f"{compress_lines}"
        f"    postrotate\n"
        f"        /usr/lib/rsyslog/rsyslog-rotate 2>/dev/null || true\n"
        f"    endscript\n"
        f"}}\n"
    )
    LOGROTATE_CONF.parent.mkdir(parents=True, exist_ok=True)
    LOGROTATE_CONF.write_text(content)


@router.get("/rotation", response_model=RotationSettings)
async def get_rotation(current_user: dict = Depends(get_current_user)):
    return _read_rotation()


@router.put("/rotation")
async def put_rotation(
    cfg: RotationSettings,
    current_user: dict = Depends(require_role([UserRole.admin])),
):
    try:
        _write_rotation(cfg)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
    log_action(current_user["username"], "settings.rotation",
               f"enabled={cfg.enabled} interval={cfg.rotate_interval} keep={cfg.rotate_count}")
    return {"status": "success", "message": "Rotation-Einstellungen gespeichert."}


# ── Maintenance window ──────────────────────────────────────────────────────

def _read_maintenance() -> MaintenanceSettings:
    if MAINTENANCE_JSON.exists():
        try:
            return MaintenanceSettings(**json.loads(MAINTENANCE_JSON.read_text()))
        except Exception:
            pass
    return MaintenanceSettings()


def _save_maintenance(cfg: MaintenanceSettings) -> None:
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    MAINTENANCE_JSON.write_text(json.dumps(cfg.model_dump(), indent=2))


def is_maintenance_active() -> bool:
    m = _read_maintenance()
    if not m.enabled:
        return False
    now = datetime.now()
    if m.pause_until:
        try:
            if now < datetime.fromisoformat(m.pause_until):
                return True
        except Exception:
            pass
    current_time = now.strftime("%H:%M")
    current_day  = now.weekday()
    for w in m.windows:
        if current_day not in w.days:
            continue
        if w.start <= w.end:
            if w.start <= current_time <= w.end:
                return True
        else:  # overnight window e.g. 22:00–06:00
            if current_time >= w.start or current_time <= w.end:
                return True
    return False


@router.get("/maintenance", response_model=MaintenanceSettings)
async def get_maintenance(current_user: dict = Depends(get_current_user)):
    return _read_maintenance()


@router.put("/maintenance")
async def put_maintenance(
    cfg: MaintenanceSettings,
    current_user: dict = Depends(require_role([UserRole.admin, UserRole.operator])),
):
    _save_maintenance(cfg)
    log_action(current_user["username"], "settings.maintenance",
               f"enabled={cfg.enabled} windows={len(cfg.windows)} pause_until={cfg.pause_until}")
    return {"status": "success", "message": "Wartungsfenster gespeichert."}


@router.post("/maintenance/pause")
async def pause_alerts(
    payload: dict,
    current_user: dict = Depends(require_role([UserRole.admin, UserRole.operator])),
):
    """Pause alerts for N hours. payload: {"hours": int}"""
    hours = int(payload.get("hours", 2))
    from datetime import timedelta
    cfg = _read_maintenance()
    cfg.enabled = True
    cfg.pause_until = (datetime.now() + timedelta(hours=hours)).isoformat()
    _save_maintenance(cfg)
    log_action(current_user["username"], "settings.maintenance.pause", f"{hours}h")
    return {"status": "success", "pause_until": cfg.pause_until}


@router.post("/maintenance/resume")
async def resume_alerts(
    current_user: dict = Depends(require_role([UserRole.admin, UserRole.operator])),
):
    cfg = _read_maintenance()
    cfg.pause_until = None
    _save_maintenance(cfg)
    log_action(current_user["username"], "settings.maintenance.resume", "")
    return {"status": "success", "message": "Pause beendet."}


@router.get("/maintenance/active")
async def maintenance_active_check(_: dict = Depends(get_current_user)):
    return {"active": is_maintenance_active()}


# ── rsyslog template ────────────────────────────────────────────────────────

@router.get("/rsyslog-template")
async def get_rsyslog_template(current_user: dict = Depends(get_current_user)):
    """Return the recommended rsyslog template snippet for host-based log directories."""
    cfg = _read_rotation()
    base = cfg.log_base_dir.rstrip("/")
    snippet = (
        '# --- Remote-Log-Eingang (einfügen in /etc/rsyslog.conf auf dem Log-Server) ---\n'
        'module(load="imtcp")\n'
        'input(type="imtcp" port="514")\n\n'
        '# Host-basiertes Verzeichnis-Schema: BASE/HOSTNAME/YYYY/MM/HOSTNAME_[IP].log\n'
        'template(name="T_REMOTE_HOST_PATH" type="string"\n'
        f'  string="{base}/%HOSTNAME%/%$YEAR%/%$MONTH%/%HOSTNAME%_[%fromhost-ip%].log")\n\n'
        'template(name="T_JSON" type="string"\n'
        '  string="{\\"timereported\\":\\"%timereported:::date-rfc3339%\\",'
        '\\"hostname\\":\\"%HOSTNAME%\\",\\"fromhost-ip\\":\\"%fromhost-ip%\\",'
        '\\"syslogfacility-text\\":\\"%syslogfacility-text%\\",'
        '\\"syslogseverity\\":\\"%syslogseverity%\\",'
        '\\"syslogfacility_text\\":\\"%syslogfacility-text%\\",'
        '\\"programname\\":\\"%programname%\\",\\"msg\\":\\"%msg:::json%\\"}\\n")\n\n'
        'if $fromhost-ip != "127.0.0.1" then {\n'
        '  action(type="omfile"\n'
        '         DynaFile="T_REMOTE_HOST_PATH"\n'
        '         template="T_JSON"\n'
        '         dirCreateMode="0755"\n'
        '         fileCreateMode="0640"\n'
        '         asyncWriting="on")\n'
        '  stop\n'
        '}\n'
        '# --- Ende ---\n'
    )
    return {"template": snippet, "base_dir": base}

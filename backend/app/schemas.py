from datetime import datetime
from enum import Enum
from pydantic import BaseModel
from typing import Literal


class TokenType(str, Enum):
    access = "access"


class Token(BaseModel):
    access_token: str
    token_type: Literal["bearer"]
    expires_at: datetime
    role: str


class TokenPayload(BaseModel):
    sub: str
    role: str
    exp: int


class LoginRequest(BaseModel):
    username: str
    password: str


class Host(BaseModel):
    name: str
    display_name: str = ""
    ip: str = ""


class User(BaseModel):
    username: str
    role: str
    email: str = ""
    hosts: list[str] = []  # empty = unrestricted (admin); non-empty = restricted to these hosts


class RsyslogConfigUpdate(BaseModel):
    content: str


class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "viewer"
    email: str = ""
    hosts: list[str] = []


class UserUpdate(BaseModel):
    password: str | None = None
    role: str | None = None
    email: str | None = None
    hosts: list[str] | None = None


class ForwardingSettings(BaseModel):
    enabled: bool = False
    protocol: str = "tcp"  # "tcp" or "udp"
    host: str = ""
    port: int = 514


class EmailSettings(BaseModel):
    enabled: bool = False
    smtp_server: str = ""
    smtp_port: int = 25
    mail_from: str = ""
    min_severity: int = 4  # 0=emerg, 1=alert, 2=crit, 3=err, 4=warning, 5=notice, 6=info
    throttle_interval: int = 300  # seconds between repeated alerts
    # Recipients derived from user.email + user.hosts assignments


class RotationSettings(BaseModel):
    enabled: bool = True
    log_base_dir: str = "/data/syslog"
    rotate_count: int = 12
    rotate_interval: str = "monthly"
    compress: bool = True
    max_size_mb: int = 0
    date_ext: bool = True


class Group(BaseModel):
    name: str
    display_name: str = ""
    members: list[str] = []
    hosts: list[str] = []


class GroupCreate(BaseModel):
    name: str
    display_name: str = ""
    members: list[str] = []
    hosts: list[str] = []


class GroupUpdate(BaseModel):
    display_name: str | None = None
    members: list[str] | None = None
    hosts: list[str] | None = None


class MaintenanceWindow(BaseModel):
    name: str = ""
    start: str = "22:00"           # HH:MM
    end: str = "06:00"             # HH:MM
    days: list[int] = [0, 1, 2, 3, 4, 5, 6]  # 0=Mon … 6=Sun


class MaintenanceSettings(BaseModel):
    enabled: bool = False
    windows: list[MaintenanceWindow] = []
    pause_until: str | None = None  # ISO datetime or null


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class ProfileUpdate(BaseModel):
    email: str | None = None

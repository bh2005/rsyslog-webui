from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, status

from .audit import log_action
from .config import settings
from .deps import get_current_user, require_role
from .models import fake_users_db, UserRole
from .schemas import LoginRequest, Token, User
from .security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


def get_user(username: str) -> dict | None:
    return fake_users_db.get(username)


def _client_ip(http: Request) -> str:
    """Client-IP für das Audit-Log (hinter dem Proxy aus X-Forwarded-For, sonst Socket-Adresse)."""
    fwd = http.headers.get("x-forwarded-for", "")
    ip = fwd.split(",")[0].strip() if fwd else ""
    if not ip and http.client:
        ip = http.client.host
    return ip[:64] or "?"


def _clean_name(name: str) -> str:
    """Nutzereingabe fürs Audit-Log: nur druckbare Zeichen, begrenzte Länge."""
    return "".join(ch for ch in name if ch.isprintable())[:64] or "?"


@router.post("/login", response_model=Token)
async def login(request: LoginRequest, http: Request):
    user = get_user(request.username)
    ip = _client_ip(http)
    if not user or not verify_password(request.password, user["hashed_password"]):
        log_action(_clean_name(request.username), "auth.login_failed", f"IP {ip}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    log_action(user["username"], "auth.login", f"IP {ip}")
    token_data = create_access_token(subject=user["username"], role=user["role"])
    return {
        "access_token": token_data["access_token"],
        "token_type": "bearer",
        "expires_at": token_data["expires_at"],
        "role": user["role"],
    }


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(http: Request, current_user: dict = Depends(get_current_user)):
    """Abmelden: das JWT ist zustandslos, der Endpoint dient dem Audit-Log."""
    log_action(current_user["username"], "auth.logout", f"IP {_client_ip(http)}")


@router.get("/me", response_model=User)
async def read_current_user(current_user: dict = Depends(get_current_user)):
    return User(**current_user)


@router.get("/admin-only")
async def admin_only(current_user: dict = Depends(require_role([UserRole.admin]))):
    return {"message": f"Hello {current_user['username']}, you have admin access."}

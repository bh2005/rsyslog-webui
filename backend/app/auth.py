from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status

from .config import settings
from .deps import get_current_user, require_role
from .models import fake_users_db, UserRole
from .schemas import LoginRequest, Token, User
from .security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


def get_user(username: str) -> dict | None:
    return fake_users_db.get(username)


@router.post("/login", response_model=Token)
async def login(request: LoginRequest):
    user = get_user(request.username)
    if not user or not verify_password(request.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = create_access_token(subject=user["username"], role=user["role"])
    return {
        "access_token": token_data["access_token"],
        "token_type": "bearer",
        "expires_at": token_data["expires_at"],
        "role": user["role"],
    }


@router.get("/me", response_model=User)
async def read_current_user(current_user: dict = Depends(get_current_user)):
    return User(**current_user)


@router.get("/admin-only")
async def admin_only(current_user: dict = Depends(require_role([UserRole.admin]))):
    return {"message": f"Hello {current_user['username']}, you have admin access."}

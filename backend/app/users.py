from fastapi import APIRouter, Depends, HTTPException, status

from .audit import log_action
from .deps import get_current_user, require_role
from .models import UserRole, UserRecord, fake_users_db
from .schemas import User, UserCreate, UserUpdate, PasswordChange, ProfileUpdate
from .security import hash_password, verify_password

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[User])
async def list_users(_: dict = Depends(require_role([UserRole.admin]))):
    return [User(username=u["username"], role=u["role"],
                 email=u.get("email", ""), hosts=u.get("hosts", []))
            for u in fake_users_db.values()]


@router.post("", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(data: UserCreate, current_user: dict = Depends(require_role([UserRole.admin]))):
    if data.username in fake_users_db:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
    if data.role not in [r.value for r in UserRole]:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid role: {data.role}")
    record: UserRecord = {
        "username": data.username,
        "hashed_password": hash_password(data.password),
        "role": UserRole(data.role),
        "email": data.email,
        "hosts": data.hosts,
    }
    fake_users_db[data.username] = record
    log_action(current_user["username"], "user.create", f"username={data.username} role={data.role}")
    return User(username=data.username, role=data.role, email=data.email, hosts=data.hosts)


@router.get("/me", response_model=User)
async def get_own_profile(current_user: dict = Depends(get_current_user)):
    u = fake_users_db.get(current_user["username"])
    return User(username=u["username"], role=u["role"],
                email=u.get("email", ""), hosts=u.get("hosts", []))


@router.put("/me/profile", response_model=User)
async def update_own_profile(
    data: ProfileUpdate,
    current_user: dict = Depends(get_current_user),
):
    username = current_user["username"]
    if data.email is not None:
        fake_users_db[username]["email"] = data.email
    log_action(username, "user.profile_update", f"email={data.email}")
    u = fake_users_db[username]
    return User(username=u["username"], role=u["role"],
                email=u.get("email", ""), hosts=u.get("hosts", []))


@router.put("/{username}", response_model=User)
async def update_user(
    username: str,
    data: UserUpdate,
    current_user: dict = Depends(require_role([UserRole.admin])),
):
    if username not in fake_users_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if data.role is not None and data.role not in [r.value for r in UserRole]:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid role: {data.role}")
    if data.role is not None and username == current_user["username"] and data.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot demote your own admin account")

    if data.password is not None:
        fake_users_db[username]["hashed_password"] = hash_password(data.password)
    if data.role is not None:
        fake_users_db[username]["role"] = UserRole(data.role)
    if data.email is not None:
        fake_users_db[username]["email"] = data.email
    if data.hosts is not None:
        fake_users_db[username]["hosts"] = data.hosts

    u = fake_users_db[username]
    changes = []
    if data.role is not None:    changes.append(f"role={data.role}")
    if data.email is not None:   changes.append(f"email={data.email}")
    if data.hosts is not None:   changes.append(f"hosts={data.hosts}")
    if data.password is not None: changes.append("password=***")
    log_action(current_user["username"], "user.update",
               f"username={username} " + " ".join(changes))
    return User(username=u["username"], role=u["role"],
                email=u.get("email", ""), hosts=u.get("hosts", []))


@router.delete("/{username}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(username: str, current_user: dict = Depends(require_role([UserRole.admin]))):
    if username not in fake_users_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if username == current_user["username"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete your own account")
    del fake_users_db[username]
    log_action(current_user["username"], "user.delete", f"username={username}")


@router.put("/me/password")
async def change_own_password(
    data: PasswordChange,
    current_user: dict = Depends(get_current_user),
):
    username = current_user["username"]
    if not verify_password(data.current_password, fake_users_db[username]["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Aktuelles Passwort ist falsch.")
    if len(data.new_password) < 6:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="Neues Passwort muss mindestens 6 Zeichen haben.")
    fake_users_db[username]["hashed_password"] = hash_password(data.new_password)
    log_action(username, "user.password_change", "eigenes Passwort geändert")
    return {"status": "success", "message": "Passwort erfolgreich geändert."}

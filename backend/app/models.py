from enum import Enum
from typing import TypedDict


class UserRole(str, Enum):
    admin = "admin"
    operator = "operator"
    viewer = "viewer"


class UserRecord(TypedDict):
    username: str
    hashed_password: str
    role: UserRole
    email: str
    hosts: list[str]  # empty = unrestricted


fake_users_db: dict[str, UserRecord] = {
    "admin": {
        "username": "admin",
        "hashed_password": "$2b$12$l8BMMuk4qxByYHvPKEqnuu6vn0F4XWLpWtBXNHb57TLa4D5G5ZLf6",  # admin123
        "role": UserRole.admin,
        "email": "",
        "hosts": [],
    },
    "operator": {
        "username": "operator",
        "hashed_password": "$2b$12$wzJafn4POLNi9p.D3GfVkuuq5VNxHeVvn0ChWYQ43vnwM5rCWqY4q",  # operator123
        "role": UserRole.operator,
        "email": "",
        "hosts": [],
    },
    "viewer": {
        "username": "viewer",
        "hashed_password": "$2b$12$cFuYpN/fzQ6mQzFpZmDSAuIfG5pxU/YMY77YHIxvlAq/037NMsleu",  # viewer123
        "role": UserRole.viewer,
        "email": "",
        "hosts": [],
    },
}

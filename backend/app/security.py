from datetime import datetime, timedelta

import bcrypt
from jose import JWTError, jwt

from .config import settings
from .schemas import TokenPayload


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def create_access_token(subject: str, role: str) -> dict:
    expires_delta = timedelta(seconds=settings.jwt_expiration_seconds)
    expire = datetime.utcnow() + expires_delta
    payload = {
        "sub": subject,
        "role": role,
        "exp": expire,
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return {"access_token": token, "expires_at": expire}


def decode_token(token: str) -> TokenPayload:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return TokenPayload(**payload)
    except JWTError as exc:
        raise ValueError("Invalid token") from exc

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import get_settings
from app.core.security import get_private_key, get_public_key


# --- Mots de passe ---
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


# --- JWT (RS256) ---
def _create_token(payload: dict, expires_in: int, token_type: str) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    to_encode = {
        **payload,
        "type": token_type,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
    }
    return jwt.encode(to_encode, get_private_key(), algorithm=settings.jwt_algorithm)


def create_access_token(payload: dict) -> str:
    return _create_token(payload, get_settings().access_token_expiration, "access")


def create_refresh_token(payload: dict) -> str:
    return _create_token(payload, get_settings().refresh_token_expiration, "refresh")


def decode_token(token: str) -> dict:
    settings = get_settings()
    return jwt.decode(token, get_public_key(), algorithms=[settings.jwt_algorithm])


def build_token_pair(user) -> dict:
    """Construit la paire access/refresh à partir d'un modèle User."""
    payload = {"id": user.id, "email": user.email, "role": user.role}
    return {
        "access_token": create_access_token(payload),
        "refresh_token": create_refresh_token(payload),
        "token_type": "bearer",
    }

from functools import lru_cache
from pathlib import Path

from fastapi.security import OAuth2PasswordBearer

from app.core.config import get_settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")


@lru_cache
def get_private_key() -> str:
    settings = get_settings()
    # Contenu PEM via env (Railway/PaaS) prioritaire, sinon lecture du fichier.
    return settings.jwt_private_key or Path(settings.jwt_private_key_path).read_text()


@lru_cache
def get_public_key() -> str:
    settings = get_settings()
    return settings.jwt_public_key or Path(settings.jwt_public_key_path).read_text()

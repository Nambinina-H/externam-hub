"""Chiffrement du mot de passe SMTP.

Clé Fernet **dérivée de la clé privée JWT** existante (SHA-256 du PEM) : aucune variable
d'environnement supplémentaire à gérer. Si la clé JWT change, l'ancien mot de passe devient
illisible → on retombe alors sur le `.env` (cf. service.resolve_smtp).
"""

import base64
import hashlib
from functools import lru_cache
from pathlib import Path

from cryptography.fernet import Fernet

from app.core.config import get_settings


@lru_cache
def _fernet() -> Fernet:
    settings = get_settings()
    pem = settings.jwt_private_key or Path(settings.jwt_private_key_path).read_text(encoding="utf-8")
    key = base64.urlsafe_b64encode(hashlib.sha256(pem.encode()).digest())
    return Fernet(key)


def encrypt(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def decrypt(token: str) -> str:
    return _fernet().decrypt(token.encode()).decode()

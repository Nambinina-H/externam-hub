"""Fixtures de test.

On configure l'environnement (clés RSA éphémères + settings) AVANT d'importer
l'app, puis on remplace la base par un SQLite in-memory via `dependency_overrides`.
"""

import os
import tempfile
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

# --- 1. Clés RSA éphémères + env, AVANT tout import de l'app ---
_keys_dir = Path(tempfile.mkdtemp())
_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
(_keys_dir / "private.pem").write_bytes(
    _key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
)
(_keys_dir / "public.pem").write_bytes(
    _key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
)

os.environ.update(
    {
        "ENVIRONMENT": "test",
        "POSTGRES_USER": "test",
        "POSTGRES_PASSWORD": "test",
        "POSTGRES_DB": "test",
        "JWT_PRIVATE_KEY_PATH": str(_keys_dir / "private.pem"),
        "JWT_PUBLIC_KEY_PATH": str(_keys_dir / "public.pem"),
        "SEED_ADMIN_EMAIL": "admin@example.com",
        "SEED_ADMIN_PASSWORD": "admin1234",
        # Tests hermétiques : pas de vrai token Meta (sinon le provider taperait l'API réelle).
        "META_ACCESS_TOKEN": "",
        "META_ADS_ACCESS_TOKEN": "",
        # ... ni de vrai SMTP (sinon un test pourrait envoyer un email réel via le compte Gmail).
        "SMTP_USER": "",
        "SMTP_PASSWORD": "",
    }
)

# --- 2. Imports de l'app (après l'env) ---
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

import app.models  # noqa: E402, F401  (enregistre les modèles sur Base)
from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402

# --- 3. Base SQLite in-memory partagée ---
_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def _create_schema():
    Base.metadata.create_all(bind=_engine)
    yield
    Base.metadata.drop_all(bind=_engine)


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def db_session():
    """Session SQLite de test (même base in-memory que le client)."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

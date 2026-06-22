from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

from app.core.config import get_settings

settings = get_settings()

# SQLite (pratique pour un démarrage local sans Postgres) a besoin de check_same_thread=False :
# les endpoints `def` tournent dans un threadpool, donc la connexion est partagée entre threads.
# Sans effet sur Postgres (connect_args vide).
_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, pool_pre_ping=True, connect_args=_connect_args)
Base = declarative_base()

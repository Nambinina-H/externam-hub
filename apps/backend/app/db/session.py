from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import engine

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Dépendance typée réutilisable dans tous les routers
DbSession = Annotated[Session, Depends(get_db)]

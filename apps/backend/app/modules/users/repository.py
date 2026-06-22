from sqlalchemy import select
from sqlalchemy.orm import Session

from app.shared.pagination import PaginationParams, paginate
from app.modules.users.models import User


class UserRepository:
    """Accès données pour l'agrégat User. Reçoit la session au constructeur,
    injecté via `Depends` (voir dependencies.py). Testable/mockable.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self.db.execute(select(User).where(User.email == email)).scalar_one_or_none()

    def create(self, user: User) -> User:
        try:
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception:
            self.db.rollback()
            raise

    def save(self, user: User) -> User:
        """Persiste les modifications d'un user déjà rattaché à la session."""
        try:
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception:
            self.db.rollback()
            raise

    def delete(self, user: User) -> None:
        try:
            self.db.delete(user)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def list_paginated(self, params: PaginationParams) -> tuple[list[User], int]:
        stmt = select(User).order_by(User.id)
        return paginate(self.db, stmt, params)

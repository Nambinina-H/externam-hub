from typing import Annotated

from fastapi import Depends

from app.db.session import DbSession
from app.modules.users.repository import UserRepository


def get_user_repository(db: DbSession) -> UserRepository:
    return UserRepository(db)


# Repository injecté, réutilisable dans les routers et autres dépendances
UserRepo = Annotated[UserRepository, Depends(get_user_repository)]

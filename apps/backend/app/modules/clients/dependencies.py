from typing import Annotated

from fastapi import Depends

from app.db.session import DbSession
from app.modules.clients.repository import ClientRepository


def get_client_repository(db: DbSession) -> ClientRepository:
    return ClientRepository(db)


# Repository injecté, réutilisable dans les routers et autres dépendances
ClientRepo = Annotated[ClientRepository, Depends(get_client_repository)]

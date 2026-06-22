from typing import Annotated

from fastapi import Depends

from app.db.session import DbSession
from app.modules.ads.repository import PortfolioRepository


def get_portfolio_repository(db: DbSession) -> PortfolioRepository:
    return PortfolioRepository(db)


PortfolioRepo = Annotated[PortfolioRepository, Depends(get_portfolio_repository)]

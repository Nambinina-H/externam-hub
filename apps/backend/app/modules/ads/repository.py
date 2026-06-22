from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.ads.models import MetaAdAccount, MetaPortfolio


class PortfolioRepository:
    """Accès données pour les portefeuilles/comptes Meta persistés (injecté via Depends)."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # --- Lecture (vue) : seulement ce qui est actif (non retiré) ---
    def active_portfolios(self) -> list[MetaPortfolio]:
        stmt = select(MetaPortfolio).where(MetaPortfolio.removed_at.is_(None)).order_by(MetaPortfolio.name)
        return list(self.db.execute(stmt).scalars().all())

    def active_accounts(self) -> list[MetaAdAccount]:
        stmt = select(MetaAdAccount).where(MetaAdAccount.removed_at.is_(None)).order_by(MetaAdAccount.name)
        return list(self.db.execute(stmt).scalars().all())

    def accounts_for_business(self, business_id: str) -> list[MetaAdAccount]:
        """Comptes actifs d'un portefeuille (pour construire le rapport par campagne)."""
        stmt = (
            select(MetaAdAccount)
            .where(MetaAdAccount.business_id == business_id, MetaAdAccount.removed_at.is_(None))
            .order_by(MetaAdAccount.name)
        )
        return list(self.db.execute(stmt).scalars().all())

    def last_synced_at(self) -> datetime | None:
        return self.db.execute(select(func.max(MetaPortfolio.last_synced_at))).scalar()

    # --- Synchro : on charge tout (y compris retirés) pour upsert/soft-remove ---
    def all_portfolios(self) -> list[MetaPortfolio]:
        return list(self.db.execute(select(MetaPortfolio)).scalars().all())

    def all_accounts(self) -> list[MetaAdAccount]:
        return list(self.db.execute(select(MetaAdAccount)).scalars().all())

    def add(self, obj) -> None:
        self.db.add(obj)

    def commit(self) -> None:
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

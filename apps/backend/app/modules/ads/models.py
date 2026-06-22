from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MetaPortfolio(Base):
    """Portefeuille (business) Meta, persisté pour un affichage rapide sans rappeler l'API.

    Source de vérité = Meta ; rafraîchi via la synchro manuelle (upsert + soft-remove).
    `removed_at` non nul = n'apparaît plus dans Meta (on garde la ligne et l'historique).
    """

    __tablename__ = "meta_portfolios"

    business_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MetaAdAccount(Base):
    """Compte publicitaire Meta (act_…), rattaché à un portefeuille."""

    __tablename__ = "meta_ad_accounts"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)  # ex. act_123456
    account_id: Mapped[str | None] = mapped_column(String(100), nullable=True)  # ex. 123456
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    account_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    business_id: Mapped[str] = mapped_column(String(100), ForeignKey("meta_portfolios.business_id"), index=True)
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

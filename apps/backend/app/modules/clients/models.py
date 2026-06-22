from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Client(Base):
    """Client de l'agence : destinataire d'un rapport ads hebdomadaire.

    Géré par l'équipe (utilisateurs authentifiés). `report_day` = jour d'envoi
    (0 = lundi … 6 = dimanche, cf. `DayOfWeekEnum`).
    """

    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    company: Mapped[str | None] = mapped_column(String(150), nullable=True)
    contact_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # Emails destinataires (plusieurs possibles) ; l'envoi laissera choisir lequel.
    emails: Mapped[list[str]] = mapped_column(JSON, default=list)
    # Portefeuille (business) Meta du client : le rapport agrège tous ses comptes pub.
    meta_business_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # Compte pub unique (override / fallback si pas de portefeuille).
    meta_ad_account_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # Campagnes (ids Meta) gérées par l'agence = incluses dans le rapport (allowlist). Vide = aucune.
    managed_campaign_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    report_day: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_report_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

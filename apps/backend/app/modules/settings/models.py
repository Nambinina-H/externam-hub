from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EmailSettings(Base):
    """Configuration SMTP gérée depuis l'interface (ligne unique, id=1).

    Le mot de passe est stocké **chiffré** (`smtp_password_enc`). Si aucune ligne n'existe
    ou que `smtp_user` est vide, l'app retombe sur les variables d'environnement (.env).
    """

    __tablename__ = "email_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    smtp_host: Mapped[str] = mapped_column(String(255), default="smtp.gmail.com")
    smtp_port: Mapped[int] = mapped_column(Integer, default=587)
    smtp_user: Mapped[str | None] = mapped_column(String(255), nullable=True)
    smtp_password_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    from_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Nom d'expéditeur (nom et prénom) — réutilisable comme variable {{expediteur}} dans les modèles.
    from_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

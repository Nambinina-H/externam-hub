from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EmailTemplate(Base):
    """Modèle d'email du rapport hebdo.

    - `client_id` NULL  → modèle de **base** (un seul).
    - `client_id` rempli → **surcharge** pour ce client (unique). Sinon le client hérite de la base.

    Seuls les blocs texte sont éditables (objet / intro / note) ; la mise en page et le tableau
    de métriques restent générés automatiquement.
    """

    __tablename__ = "email_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=True, unique=True
    )
    subject: Mapped[str] = mapped_column(String(300))
    intro: Mapped[str] = mapped_column(Text)
    closing: Mapped[str] = mapped_column(Text)
    # Bloc signature (texte libre saisi par l'agence). Le séparateur « -- » est ajouté au rendu.
    signature: Mapped[str] = mapped_column(Text, default="", server_default="")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

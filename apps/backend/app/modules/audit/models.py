from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditLog(Base):
    """Journal d'audit : une ligne par action mutante (POST/PUT/PATCH/DELETE) sur l'API.

    Alimenté automatiquement par un middleware → couvre les features actuelles ET à venir
    sans instrumentation manuelle. L'acteur est **dénormalisé** (email/role copiés) pour
    rester lisible même après la suppression de l'utilisateur. Aucune donnée de corps n'est
    enregistrée (les requêtes peuvent contenir des mots de passe).
    """

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    actor_email: Mapped[str | None] = mapped_column(String(150), nullable=True)
    actor_role: Mapped[str | None] = mapped_column(String(50), nullable=True)
    method: Mapped[str] = mapped_column(String(10))
    path: Mapped[str] = mapped_column(String(500))
    action: Mapped[str] = mapped_column(String(255))
    status_code: Mapped[int] = mapped_column(Integer)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

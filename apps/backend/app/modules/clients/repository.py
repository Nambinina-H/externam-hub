from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.shared.pagination import PaginationParams, paginate
from app.modules.clients.models import Client


class ClientRepository:
    """Accès données pour l'agrégat Client. Reçoit la session au constructeur,
    injecté via `Depends` (voir dependencies.py).
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, client_id: int) -> Client | None:
        return self.db.get(Client, client_id)

    def create(self, client: Client) -> Client:
        try:
            self.db.add(client)
            self.db.commit()
            self.db.refresh(client)
            return client
        except Exception:
            self.db.rollback()
            raise

    def save(self, client: Client) -> Client:
        """Persiste les modifications d'un client déjà rattaché à la session."""
        try:
            self.db.commit()
            self.db.refresh(client)
            return client
        except Exception:
            self.db.rollback()
            raise

    def delete(self, client: Client) -> None:
        try:
            self.db.delete(client)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def list_paginated(self, params: PaginationParams) -> tuple[list[Client], int]:
        stmt = select(Client).order_by(Client.id)
        return paginate(self.db, stmt, params)

    def list_all(self) -> list[Client]:
        """Tous les clients (pour l'upsert d'import : retrouver un client par nom)."""
        return list(self.db.execute(select(Client).order_by(Client.id)).scalars().all())

    def list_active_by_day(self, day: int) -> list[Client]:
        """Clients actifs dont le jour d'envoi correspond à `day` (0 = lundi … 6 = dimanche)."""
        stmt = select(Client).where(Client.is_active.is_(True), Client.report_day == day).order_by(Client.id)
        return list(self.db.execute(stmt).scalars().all())

    def mark_report_sent(self, client: Client) -> None:
        client.last_report_sent_at = datetime.now(timezone.utc)
        self.db.commit()

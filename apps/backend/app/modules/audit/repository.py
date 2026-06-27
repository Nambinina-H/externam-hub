from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.audit.models import AuditLog
from app.shared.pagination import PaginationParams, paginate


class AuditRepository:
    """Accès données du journal d'audit (injecté via Depends)."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, **fields) -> AuditLog:
        log = AuditLog(**fields)
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def list_paginated(
        self,
        params: PaginationParams,
        *,
        method: str | None = None,
        actor: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> tuple[list[AuditLog], int]:
        stmt = select(AuditLog).order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        if method:
            stmt = stmt.where(AuditLog.method == method)
        if actor:
            stmt = stmt.where(AuditLog.actor_email.ilike(f"%{actor}%"))
        if date_from:
            stmt = stmt.where(func.date(AuditLog.created_at) >= date_from)
        if date_to:
            stmt = stmt.where(func.date(AuditLog.created_at) <= date_to)
        return paginate(self.db, stmt, params)

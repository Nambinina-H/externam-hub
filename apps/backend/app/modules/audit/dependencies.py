from typing import Annotated

from fastapi import Depends

from app.db.session import DbSession
from app.modules.audit.repository import AuditRepository


def get_audit_repository(db: DbSession) -> AuditRepository:
    return AuditRepository(db)


AuditRepo = Annotated[AuditRepository, Depends(get_audit_repository)]

from datetime import date

from app.modules.audit.repository import AuditRepository
from app.modules.audit.schemas import AuditLogPublic
from app.shared.pagination import Page, PaginationParams


def list_logs(
    repo: AuditRepository,
    params: PaginationParams,
    *,
    method: str | None = None,
    actor: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> Page[AuditLogPublic]:
    items, total = repo.list_paginated(
        params, method=method, actor=actor, date_from=date_from, date_to=date_to
    )
    return Page[AuditLogPublic](items=items, total=total, page=params.page, size=params.size)

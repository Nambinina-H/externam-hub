from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.modules.audit import service
from app.modules.audit.dependencies import AuditRepo
from app.modules.audit.schemas import AuditLogPublic
from app.modules.auth.dependencies import require_superadmin
from app.shared.pagination import Page, PaginationDep

# Réservé aux admins (SUPERADMIN / ADMIN).
router = APIRouter(prefix="/audit", tags=["Audit"], dependencies=[Depends(require_superadmin)])


@router.get("", response_model=Page[AuditLogPublic])
def list_audit(
    repo: AuditRepo,
    params: PaginationDep,
    method: Annotated[str | None, Query(description="Filtre par méthode HTTP (POST, DELETE…)")] = None,
    actor: Annotated[str | None, Query(description="Filtre par email d'acteur (sous-chaîne)")] = None,
    date_from: Annotated[date | None, Query(description="Depuis cette date (incluse)")] = None,
    date_to: Annotated[date | None, Query(description="Jusqu'à cette date (incluse)")] = None,
):
    """Journal d'audit — actions mutantes, les plus récentes d'abord (admin uniquement)."""
    return service.list_logs(repo, params, method=method, actor=actor, date_from=date_from, date_to=date_to)

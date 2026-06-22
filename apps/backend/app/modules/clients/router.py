from fastapi import APIRouter, Depends, status

from app.core.errors import BadRequestError
from app.db.session import DbSession
from app.shared.pagination import Page, PaginationDep
from app.modules.ads import service as ads_service
from app.modules.ads.dependencies import PortfolioRepo
from app.modules.auth.dependencies import require_meta_ads
from app.modules.clients import service
from app.modules.clients.dependencies import ClientRepo
from app.modules.clients.schemas import (
    ClientCreateSchema,
    ClientPublicSchema,
    ClientUpdateSchema,
    ImportPreviewRequest,
    ImportRequest,
    SendReportRequest,
)
from app.modules.reports import service as reports_service

# Toutes les routes clients sont réservées à l'équipe (admin/superadmin).
router = APIRouter(
    prefix="/clients",
    tags=["Clients"],
    dependencies=[Depends(require_meta_ads)],
)


@router.get("", response_model=Page[ClientPublicSchema])
def list_clients(repo: ClientRepo, params: PaginationDep):
    return service.list_clients(repo, params)


@router.post("", response_model=ClientPublicSchema, status_code=status.HTTP_201_CREATED)
def create_client(payload: ClientCreateSchema, repo: ClientRepo):
    return service.create_client(repo, payload)


# --- Import CSV (avant /{client_id} pour ne pas capter "import" comme un id) ---


@router.post("/import/preview")
def import_preview(payload: ImportPreviewRequest):
    """Renvoie les en-têtes + un échantillon pour construire le mapping de colonnes."""
    return service.preview_import(payload.csv)


@router.post("/import")
def import_csv(payload: ImportRequest, repo: ClientRepo, portfolio_repo: PortfolioRepo):
    """Crée/maj les clients depuis le CSV ; lie aux portefeuilles si `auto_link`."""
    result = service.import_clients(repo, payload.csv, payload.mapping)
    if payload.auto_link:
        portfolios = ads_service.list_portfolios(portfolio_repo)["portfolios"]
        result["linked"] = service.auto_link_clients(repo, portfolios)
    return result


@router.get("/{client_id}", response_model=ClientPublicSchema)
def get_client(client_id: int, repo: ClientRepo):
    return ClientPublicSchema.model_validate(service.get_client(repo, client_id))


@router.patch("/{client_id}", response_model=ClientPublicSchema)
def update_client(client_id: int, payload: ClientUpdateSchema, repo: ClientRepo):
    return service.update_client(repo, client_id, payload)


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(client_id: int, repo: ClientRepo):
    service.delete_client(repo, client_id)


@router.get("/{client_id}/report-preview")
def report_preview(client_id: int, repo: ClientRepo, db: DbSession):
    """Rend le HTML du rapport hebdo du client (aperçu, sans envoi)."""
    client = service.get_client(repo, client_id)
    return reports_service.preview_report(db, client)


@router.post("/{client_id}/send-report")
def send_report_now(client_id: int, repo: ClientRepo, db: DbSession, payload: SendReportRequest | None = None):
    """Construit et envoie le rapport ads du client (aux emails choisis, sinon à tous)."""
    client = service.get_client(repo, client_id)
    if not client.emails:
        raise BadRequestError("Le client n'a pas d'email destinataire.")
    to = [str(email) for email in payload.to] if payload and payload.to else None
    recipients = reports_service.send_report_for_client(db, client, to=to)
    return {"status": "sent", "client_id": client.id, "recipients": recipients}

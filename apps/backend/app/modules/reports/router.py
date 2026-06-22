from datetime import date

from fastapi import APIRouter, Depends

from app.core.errors import NotFoundError
from app.db.session import DbSession
from app.modules.auth.dependencies import require_meta_ads
from app.modules.clients.dependencies import ClientRepo
from app.modules.clients.service import get_client
from app.modules.reports import service
from app.modules.reports.dependencies import EmailTemplateRepo
from app.modules.reports.schemas import EmailTemplateSchema, EmailTemplateView, TemplatePreviewRequest

router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
    dependencies=[Depends(require_meta_ads)],
)


@router.post("/send-day")
def send_day(db: DbSession):
    """Envoie le rapport hebdo à tous les clients actifs dont le jour d'envoi = aujourd'hui."""
    today = date.today()
    result = service.send_weekly_reports_for_day(db, today.weekday(), today=today)
    return {**result, "weekday": today.weekday()}


# --- Modèle d'email (base + surcharges par client) ---


@router.get("/template/placeholders")
def template_placeholders():
    """Liste des placeholders insérables dans l'éditeur."""
    return [{"key": key, "label": label} for key, label in service.PLACEHOLDERS.items()]


@router.get("/template/overrides")
def template_overrides(repo: EmailTemplateRepo) -> list[int]:
    """Ids des clients ayant une surcharge de modèle."""
    return repo.override_client_ids()


@router.get("/template", response_model=EmailTemplateView)
def get_base_template(repo: EmailTemplateRepo):
    return service.get_base_view(repo)


@router.put("/template", response_model=EmailTemplateView)
def update_base_template(payload: EmailTemplateSchema, repo: EmailTemplateRepo):
    return service.update_base(repo, payload)


@router.post("/template/preview")
def preview_template(payload: TemplatePreviewRequest, repo: ClientRepo, db: DbSession):
    """Aperçu en direct d'un modèle (données d'exemple, instantané)."""
    client = get_client(repo, payload.client_id) if payload.client_id else None
    return service.preview_template(db, client, payload)


@router.get("/template/client/{client_id}", response_model=EmailTemplateView)
def get_client_template(client_id: int, repo: EmailTemplateRepo):
    return service.get_client_view(repo, client_id)


@router.put("/template/client/{client_id}", response_model=EmailTemplateView)
def upsert_client_template(client_id: int, payload: EmailTemplateSchema, repo: EmailTemplateRepo, client_repo: ClientRepo):
    if not client_repo.get_by_id(client_id):
        raise NotFoundError("Client introuvable")
    return service.upsert_override(repo, client_id, payload)


@router.delete("/template/client/{client_id}")
def delete_client_template(client_id: int, repo: EmailTemplateRepo):
    """Supprime la surcharge → le client revient au modèle de base."""
    service.delete_override(repo, client_id)
    return {"status": "reverted", "client_id": client_id}

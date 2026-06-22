from fastapi import APIRouter, Depends

from app.modules.auth.dependencies import require_meta_ads
from app.modules.settings import service
from app.modules.settings.dependencies import EmailSettingsRepo
from app.modules.settings.schemas import EmailSettingsPublic, EmailSettingsUpdate, TestEmailRequest

router = APIRouter(
    prefix="/settings",
    tags=["Settings"],
    dependencies=[Depends(require_meta_ads)],
)


@router.get("/email", response_model=EmailSettingsPublic)
def get_email_settings(repo: EmailSettingsRepo):
    return service.get_public(repo)


@router.put("/email", response_model=EmailSettingsPublic)
def update_email_settings(payload: EmailSettingsUpdate, repo: EmailSettingsRepo):
    return service.update_settings(repo, payload)


@router.post("/email/test")
def test_email_settings(payload: TestEmailRequest):
    """Envoie un email de test à l'adresse choisie (jamais aux clients de la base)."""
    service.send_test_email(str(payload.to))
    return {"status": "sent", "to": str(payload.to)}

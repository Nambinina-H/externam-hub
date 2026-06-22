"""Endpoints de diagnostic Meta Ads (réservés équipe).

Servent à valider le token + explorer la hiérarchie (businesses -> comptes -> campagnes)
et un échantillon d'insights. La logique métier du rapport hebdo reste dans reports/.
"""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query

from app.core.config import get_settings
from app.core.errors import BadRequestError
from app.modules.ads import provider, service
from app.modules.ads.dependencies import PortfolioRepo
from app.modules.auth.dependencies import require_meta_ads

router = APIRouter(
    prefix="/ads",
    tags=["Ads"],
    dependencies=[Depends(require_meta_ads)],
)


def _client():
    settings = get_settings()
    if not settings.meta_access_token:
        raise BadRequestError("META_ACCESS_TOKEN non configuré (provider en mode stub).")
    from app.modules.ads.meta_client import MetaAdsClient

    return MetaAdsClient(
        settings.meta_access_token,
        version=settings.meta_graph_version,
        app_secret=settings.meta_app_secret or None,
        timeout=settings.meta_api_timeout,
        max_retries=settings.meta_max_retries,
    )


@router.get("/businesses")
def list_businesses():
    with _client() as client:
        return client.list_businesses()


@router.get("/accounts")
def list_accounts(business_id: str | None = Query(default=None)):
    with _client() as client:
        return client.list_ad_accounts(business_id)


@router.get("/portfolios")
def list_portfolios(repo: PortfolioRepo):
    """Portefeuilles persistés (lecture base, rapide). Utiliser POST /portfolios/sync pour rafraîchir."""
    return service.list_portfolios(repo)


@router.post("/portfolios/sync")
def sync_portfolios(repo: PortfolioRepo):
    """Rafraîchit la base depuis Meta : upsert des présents + soft-remove des disparus."""
    settings = get_settings()
    with _client() as client:
        return service.sync_portfolios(repo, client, settings.meta_business_id or None)


@router.get("/accounts/{account_id}/campaigns")
def list_campaigns(account_id: str):
    """Campagnes d'un compte pub (vraie API Meta si token configuré, sinon données fictives)."""
    return provider.get_account_campaigns(account_id)


@router.get("/accounts/{account_id}/insights")
def get_insights(
    account_id: str,
    since: date | None = Query(default=None),
    until: date | None = Query(default=None),
    daily: bool = Query(default=False),
):
    """Insights d'un compte. Par défaut : agrégat des 7 derniers jours ; `daily=true` -> série quotidienne."""
    today = date.today()
    until = until or today
    since = since or (until - timedelta(days=6))
    with _client() as client:
        return client.get_insights(account_id, since=since, until=until, time_increment=1 if daily else None)

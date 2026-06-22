"""Fournisseur de métriques ads.

- **Avec** `META_ACCESS_TOKEN` : `get_weekly_metrics` appelle la vraie Meta Marketing API
  (`/act_{id}/insights`, agrégat sur la semaine) via `app.modules.ads.meta_client`.
- **Sans** token : fallback sur un **stub déterministe** (SHA-256) — dev/test/offline,
  même esprit que `send_email()` qui log si SMTP non configuré. La signature ne change pas.
"""

import hashlib
import logging
from dataclasses import dataclass
from datetime import date, timedelta

from app.core.config import get_settings

logger = logging.getLogger("ads")

# Objectif de conversion (par client) -> action_type Meta à sommer. Le client choisit son objectif
# (cf. ConversionGoalEnum) car chaque campagne track des actions différentes selon son objectif.
CONVERSION_GOAL_ACTIONS = {
    "purchase": ("purchase", "omni_purchase", "offsite_conversion.fb_pixel_purchase"),
    "lead": ("lead", "offsite_conversion.fb_pixel_lead", "onsite_conversion.lead_grouped"),
    "add_to_cart": ("add_to_cart", "omni_add_to_cart", "offsite_conversion.fb_pixel_add_to_cart", "onsite_web_add_to_cart"),
    "checkout": ("initiate_checkout", "omni_initiated_checkout", "offsite_conversion.fb_pixel_initiate_checkout"),
    "call": ("click_to_call_call_confirm", "call_confirm_grouped"),
    "landing_page_view": ("landing_page_view", "omni_landing_page_view"),
    "message": ("onsite_conversion.messaging_conversation_started_7d", "onsite_conversion.total_messaging_connection"),
}
DEFAULT_CONVERSION_GOAL = "purchase"


@dataclass
class WeeklyMetrics:
    spend: float
    impressions: int
    clicks: int
    conversions: int
    ctr: float  # taux de clic en %
    cpc: float  # coût par clic


def _f(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _i(value) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _extract_conversions(row, conversion_goal=DEFAULT_CONVERSION_GOAL) -> int:
    """Somme les `value` du tableau `actions` correspondant à l'objectif du client."""
    action_types = CONVERSION_GOAL_ACTIONS.get(conversion_goal, CONVERSION_GOAL_ACTIONS[DEFAULT_CONVERSION_GOAL])
    total = 0.0
    for action in row.get("actions") or []:
        if action.get("action_type") in action_types:
            total += _f(action.get("value"))
    return int(round(total))


def get_weekly_metrics(
    account_id: str | None, start: date, end: date, conversion_goal: str = DEFAULT_CONVERSION_GOAL
) -> WeeklyMetrics:
    """Métriques agrégées sur la période [start, end] (semaine), pour un compte ads.

    `conversion_goal` (par client) choisit quels action_type comptent comme conversion.
    """
    settings = get_settings()

    if not settings.meta_access_token or not account_id:
        return _stub_weekly_metrics(account_id, start, end)

    # Import paresseux (httpx) — l'app démarre même si la lib manque, et le stub reste autonome.
    from app.modules.ads.meta_client import MetaAdsClient

    with MetaAdsClient(
        settings.meta_access_token,
        version=settings.meta_graph_version,
        app_secret=settings.meta_app_secret or None,
        timeout=settings.meta_api_timeout,
        max_retries=settings.meta_max_retries,
    ) as client:
        # Agrégat de la semaine = 1 seule ligne (time_increment non fourni -> all_days).
        rows = client.get_insights(account_id, since=start, until=end, level="account", time_increment=None)

    if not rows:
        return WeeklyMetrics(0.0, 0, 0, 0, 0.0, 0.0)

    row = rows[0]
    spend = _f(row.get("spend"))
    impressions = _i(row.get("impressions"))
    clicks = _i(row.get("clicks"))
    conversions = _extract_conversions(row, conversion_goal)
    ctr = _f(row.get("ctr")) or (clicks / impressions * 100 if impressions else 0.0)
    cpc = _f(row.get("cpc")) or (spend / clicks if clicks else 0.0)

    return WeeklyMetrics(round(spend, 2), impressions, clicks, conversions, round(ctr, 2), round(cpc, 2))


def get_business_weekly_metrics(
    business_id: str | None, start: date, end: date, conversion_goal: str = DEFAULT_CONVERSION_GOAL
) -> WeeklyMetrics:
    """Métriques agrégées sur TOUS les comptes pub du portefeuille `business_id` (1 client = 1 portefeuille)."""
    settings = get_settings()

    if not settings.meta_access_token or not business_id:
        return _stub_weekly_metrics(business_id, start, end)

    from app.modules.ads.meta_client import MetaAdsClient

    spend = 0.0
    impressions = clicks = conversions = 0
    with MetaAdsClient(
        settings.meta_access_token,
        version=settings.meta_graph_version,
        app_secret=settings.meta_app_secret or None,
        timeout=settings.meta_api_timeout,
        max_retries=settings.meta_max_retries,
    ) as client:
        for account_id in client.accounts_in_business(business_id, settings.meta_business_id or None):
            rows = client.get_insights(account_id, since=start, until=end, level="account", time_increment=None)
            if not rows:
                continue
            row = rows[0]
            spend += _f(row.get("spend"))
            impressions += _i(row.get("impressions"))
            clicks += _i(row.get("clicks"))
            conversions += _extract_conversions(row, conversion_goal)

    ctr = (clicks / impressions * 100) if impressions else 0.0
    cpc = (spend / clicks) if clicks else 0.0
    return WeeklyMetrics(round(spend, 2), impressions, clicks, conversions, round(ctr, 2), round(cpc, 2))


def _stub_weekly_metrics(account_id: str | None, start: date, end: date) -> WeeklyMetrics:
    """Valeurs déterministes (dérivées de l'account_id + semaine) — reproductibles, sans credentials."""
    seed_src = f"{account_id or 'no-account'}:{start.isoformat()}:{end.isoformat()}"
    h = int(hashlib.sha256(seed_src.encode()).hexdigest(), 16)

    impressions = 5_000 + (h % 20_000)
    clicks = 50 + (h % 800)
    spend = round(20 + (h % 500) + (h % 100) / 10, 2)
    conversions = 1 + (h % 40)
    ctr = round((clicks / impressions) * 100, 2) if impressions else 0.0
    cpc = round(spend / clicks, 2) if clicks else 0.0

    return WeeklyMetrics(spend, impressions, clicks, conversions, ctr, cpc)


# --- Campagnes (catalogue) -------------------------------------------------
#
# Étape 1 du rapport par campagne : lister les campagnes d'un compte pour pouvoir,
# ensuite, choisir lesquelles sont gérées par l'agence (incluses dans le rapport).

# Objectif Meta (ODAX récents ET anciens) -> libellé FR + famille de métriques.
OBJECTIVE_LABELS = {
    "OUTCOME_SALES": "Ventes",
    "CONVERSIONS": "Ventes",
    "PRODUCT_CATALOG_SALES": "Ventes",
    "OUTCOME_LEADS": "Prospects",
    "LEAD_GENERATION": "Prospects",
    "OUTCOME_TRAFFIC": "Trafic",
    "LINK_CLICKS": "Trafic",
    "TRAFFIC": "Trafic",
    "STORE_VISITS": "Trafic",
    "OUTCOME_AWARENESS": "Notoriété",
    "BRAND_AWARENESS": "Notoriété",
    "REACH": "Notoriété",
    "OUTCOME_ENGAGEMENT": "Interactions",
    "POST_ENGAGEMENT": "Interactions",
    "PAGE_LIKES": "Interactions",
    "VIDEO_VIEWS": "Interactions",
    "MESSAGES": "Interactions",
    "EVENT_RESPONSES": "Interactions",
    "OUTCOME_APP_PROMOTION": "Promotion d'app",
    "APP_INSTALLS": "Promotion d'app",
}


def objective_label(objective: str | None) -> str:
    if not objective:
        return "—"
    return OBJECTIVE_LABELS.get(objective, objective.replace("OUTCOME_", "").replace("_", " ").title())


def _normalize_campaign(c: dict) -> dict:
    objective = c.get("objective")
    return {
        "id": c.get("id"),
        "name": c.get("name"),
        "objective": objective,
        "objective_label": objective_label(objective),
        "status": c.get("status"),
        "effective_status": c.get("effective_status") or c.get("status"),
    }


def get_account_campaigns(account_id: str | None) -> list[dict]:
    """Campagnes d'un compte pub. Vraie API Meta si `META_ACCESS_TOKEN`, sinon stub déterministe."""
    settings = get_settings()

    if not settings.meta_access_token or not account_id:
        return [_normalize_campaign(c) for c in _stub_campaigns(account_id)]

    from app.modules.ads.meta_client import MetaAdsClient

    with MetaAdsClient(
        settings.meta_access_token,
        version=settings.meta_graph_version,
        app_secret=settings.meta_app_secret or None,
        timeout=settings.meta_api_timeout,
        max_retries=settings.meta_max_retries,
    ) as client:
        return [_normalize_campaign(c) for c in client.list_campaigns(account_id)]


# Campagnes fictives (dev/offline) — un mélange d'objectifs pour tester le tri par type.
_STUB_CAMPAIGNS = (
    ("Acquisition — Soldes", "OUTCOME_SALES", "ACTIVE"),
    ("Retargeting panier abandonné", "OUTCOME_SALES", "ACTIVE"),
    ("Génération de prospects", "OUTCOME_LEADS", "ACTIVE"),
    ("Trafic site web", "OUTCOME_TRAFFIC", "PAUSED"),
    ("Notoriété de la marque", "OUTCOME_AWARENESS", "ACTIVE"),
    ("Messages & interactions", "OUTCOME_ENGAGEMENT", "ACTIVE"),
)


def _stub_campaigns(account_id: str | None) -> list[dict]:
    """2 à 5 campagnes fictives déterministes (dérivées de l'account_id)."""
    h = int(hashlib.sha256((account_id or "no-account").encode()).hexdigest(), 16)
    count = 2 + (h % 4)
    base = (account_id or "acct").replace("act_", "")
    out = []
    for i in range(count):
        name, objective, status = _STUB_CAMPAIGNS[(h + i) % len(_STUB_CAMPAIGNS)]
        out.append(
            {"id": f"stub_{base}_{i}", "name": name, "objective": objective, "status": status, "effective_status": status}
        )
    return out


# --- Rapport PAR CAMPAGNE (jour par jour + total semaine) -------------------
#
# - Le « résultat » dépend de l'objectif : (libellé, action_types à sommer ; None = portée).
# - Clics / CPC / CTR = CLICS SUR UN LIEN (inline_link_clicks) ; attribution 7 j clic.
# - Total semaine pris en AGRÉGAT (pas la somme des jours) -> portée & CTR unique corrects.

_OBJECTIVE_RESULT = {
    "OUTCOME_SALES": ("Achats", ("purchase", "omni_purchase", "offsite_conversion.fb_pixel_purchase")),
    "CONVERSIONS": ("Achats", ("purchase", "omni_purchase", "offsite_conversion.fb_pixel_purchase")),
    "PRODUCT_CATALOG_SALES": ("Achats", ("purchase", "omni_purchase", "offsite_conversion.fb_pixel_purchase")),
    "OUTCOME_LEADS": ("Prospects", ("lead", "offsite_conversion.fb_pixel_lead", "onsite_conversion.lead_grouped")),
    "LEAD_GENERATION": ("Prospects", ("lead", "offsite_conversion.fb_pixel_lead", "onsite_conversion.lead_grouped")),
    "OUTCOME_TRAFFIC": ("Clics sur le lien", ("link_click",)),
    "LINK_CLICKS": ("Clics sur le lien", ("link_click",)),
    "TRAFFIC": ("Clics sur le lien", ("link_click",)),
    "OUTCOME_ENGAGEMENT": ("Interactions", ("post_engagement", "onsite_conversion.messaging_conversation_started_7d")),
    "POST_ENGAGEMENT": ("Interactions", ("post_engagement",)),
    "MESSAGES": ("Conversations", ("onsite_conversion.messaging_conversation_started_7d",)),
    "VIDEO_VIEWS": ("Vues de vidéo", ("video_view",)),
    "OUTCOME_AWARENESS": ("Portée", None),
    "BRAND_AWARENESS": ("Portée", None),
    "REACH": ("Portée", None),
}
_DEFAULT_RESULT = ("Résultats", ("purchase", "lead", "link_click"))
_SALES_OBJECTIVES = {"OUTCOME_SALES", "CONVERSIONS", "PRODUCT_CATALOG_SALES"}

_ATTRIBUTION = ("7d_click", "1d_view")  # = « 7 jours clic ou 1 jour vue » (réglage Ads Manager observé)
_DAY_FR = ("Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim")
_DAILY_FIELDS = ("campaign_id", "spend", "impressions", "inline_link_clicks", "reach", "actions")
_WEEKLY_FIELDS = (
    "campaign_id", "spend", "impressions", "inline_link_clicks", "reach",
    "unique_inline_link_click_ctr", "actions", "purchase_roas",
)


@dataclass
class CampaignDay:
    label: str  # ex. "Lun 08/06"
    spend: float
    impressions: int
    link_clicks: int
    ctr: float  # CTR (clics sur un lien) du jour
    result: int  # résultat du jour selon l'objectif


@dataclass
class CampaignReport:
    id: str
    name: str
    objective: str | None
    objective_label: str
    result_label: str
    # Totaux de la semaine (agrégat Meta)
    spend: float
    budget: float | None
    impressions: int
    link_clicks: int
    cpc: float
    unique_ctr: float
    reach: int
    result: int
    cost_per_result: float
    roas: float | None
    days: list[CampaignDay]


def _result_count(actions, action_types) -> int:
    """Nombre de résultats = MAX parmi les action_types de la famille.

    Meta renvoie souvent les MÊMES résultats sous plusieurs alias (ex. `lead` ET
    `onsite_conversion.lead_grouped`, ou `purchase` ET `omni_purchase`). Les SOMMER
    double-compterait ; on prend donc le plus grand, qui correspond à « Résultats » dans Ads Manager.
    """
    best = 0.0
    for action in actions or []:
        if action.get("action_type") in action_types:
            best = max(best, _f(action.get("value")))
    return int(round(best))


def _roas(row) -> float | None:
    for item in row.get("purchase_roas") or []:
        value = _f(item.get("value"))
        if value:
            return round(value, 2)
    return None


def _day_label(d: date) -> str:
    return f"{_DAY_FR[d.weekday()]} {d:%d/%m}"


def _date_range(start: date, end: date):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def _campaign_budget(campaign: dict, start: date, end: date) -> float | None:
    """Budget indicatif sur la période (Meta renvoie les budgets en centimes)."""
    days = (end - start).days + 1
    daily = campaign.get("daily_budget")
    if daily:
        return round(_f(daily) / 100 * days, 2)
    lifetime = campaign.get("lifetime_budget")
    if lifetime:
        return round(_f(lifetime) / 100, 2)
    return None


def _build_campaign_report(campaign: dict, week_row: dict, daily_rows: list, start: date, end: date) -> CampaignReport:
    objective = campaign.get("objective")
    result_label, action_types = _OBJECTIVE_RESULT.get(objective, _DEFAULT_RESULT)

    # Total semaine (agrégat)
    spend = _f(week_row.get("spend"))
    impressions = _i(week_row.get("impressions"))
    link_clicks = _i(week_row.get("inline_link_clicks"))
    reach = _i(week_row.get("reach"))
    unique_ctr = _f(week_row.get("unique_inline_link_click_ctr"))
    week_result = reach if action_types is None else _result_count(week_row.get("actions"), action_types)
    cpc = round(spend / link_clicks, 2) if link_clicks else 0.0
    cost_per_result = round(spend / week_result, 2) if week_result else 0.0
    roas = _roas(week_row) if objective in _SALES_OBJECTIVES else None

    # Série jour par jour (jour sans diffusion -> 0)
    rows_by_date = {r.get("date_start"): r for r in daily_rows}
    days = []
    for d in _date_range(start, end):
        r = rows_by_date.get(d.isoformat(), {})
        d_impr = _i(r.get("impressions"))
        d_clicks = _i(r.get("inline_link_clicks"))
        d_result = _i(r.get("reach")) if action_types is None else _result_count(r.get("actions"), action_types)
        days.append(
            CampaignDay(
                label=_day_label(d),
                spend=round(_f(r.get("spend")), 2),
                impressions=d_impr,
                link_clicks=d_clicks,
                ctr=round(d_clicks / d_impr * 100, 2) if d_impr else 0.0,
                result=d_result,
            )
        )

    return CampaignReport(
        id=campaign.get("id"),
        name=campaign.get("name"),
        objective=objective,
        objective_label=objective_label(objective),
        result_label=result_label,
        spend=round(spend, 2),
        budget=_campaign_budget(campaign, start, end),
        impressions=impressions,
        link_clicks=link_clicks,
        cpc=cpc,
        unique_ctr=round(unique_ctr, 2),
        reach=reach,
        result=week_result,
        cost_per_result=cost_per_result,
        roas=roas,
        days=days,
    )


def get_campaign_reports(account_id: str | None, start: date, end: date) -> list[CampaignReport]:
    """Rapport par campagne (jour par jour + total semaine). Vraie API Meta si token, sinon stub."""
    settings = get_settings()

    if not settings.meta_access_token or not account_id:
        return _stub_campaign_reports(account_id, start, end)

    from app.modules.ads.meta_client import MetaAdsClient

    with MetaAdsClient(
        settings.meta_access_token,
        version=settings.meta_graph_version,
        app_secret=settings.meta_app_secret or None,
        timeout=settings.meta_api_timeout,
        max_retries=settings.meta_max_retries,
    ) as client:
        campaigns = client.list_campaigns(account_id)
        daily = client.get_insights(
            account_id, since=start, until=end, level="campaign", time_increment=1,
            fields=_DAILY_FIELDS, action_attribution_windows=_ATTRIBUTION,
        )
        weekly = client.get_insights(
            account_id, since=start, until=end, level="campaign", time_increment=None,
            fields=_WEEKLY_FIELDS, action_attribution_windows=_ATTRIBUTION,
        )

    daily_by_campaign: dict = {}
    for row in daily:
        daily_by_campaign.setdefault(row.get("campaign_id"), []).append(row)
    weekly_by_campaign = {row.get("campaign_id"): row for row in weekly}

    return [
        _build_campaign_report(
            c, weekly_by_campaign.get(c.get("id"), {}), daily_by_campaign.get(c.get("id"), []), start, end
        )
        for c in campaigns
    ]


def sample_campaign_reports(start: date, end: date) -> list[CampaignReport]:
    """Données d'exemple (toujours stub) pour l'aperçu live de l'éditeur de modèle."""
    return _stub_campaign_reports("act_apercu", start, end)


def _stub_campaign_reports(account_id: str | None, start: date, end: date) -> list[CampaignReport]:
    """7 jours + total semaine déterministes (dev/offline)."""
    reports = []
    for campaign in _stub_campaigns(account_id):
        objective = campaign["objective"]
        result_label, action_types = _OBJECTIVE_RESULT.get(objective, _DEFAULT_RESULT)
        seed = int(hashlib.sha256(campaign["id"].encode()).hexdigest(), 16)
        daily_budget_eur = 20 + (seed % 50)

        days = []
        tot_spend = 0.0
        tot_impr = tot_clicks = tot_result = 0
        for d in _date_range(start, end):
            h = int(hashlib.sha256(f"{campaign['id']}:{d.isoformat()}".encode()).hexdigest(), 16)
            impr = 3_000 + (h % 5_000)
            clicks = 40 + (h % 220)
            spend = round(min(float(daily_budget_eur), 10 + (h % 60) + (h % 100) / 10), 2)
            day_result = int(impr * 0.7) if action_types is None else 1 + (h % 8)
            days.append(
                CampaignDay(
                    label=_day_label(d),
                    spend=spend,
                    impressions=impr,
                    link_clicks=clicks,
                    ctr=round(clicks / impr * 100, 2) if impr else 0.0,
                    result=day_result,
                )
            )
            tot_spend += spend
            tot_impr += impr
            tot_clicks += clicks
            tot_result += 0 if action_types is None else day_result

        # Portée & CTR unique de la semaine = personnes uniques (< somme des jours).
        week_reach = int(tot_impr * 0.45)
        week_result = week_reach if action_types is None else tot_result
        reports.append(
            CampaignReport(
                id=campaign["id"],
                name=campaign["name"],
                objective=objective,
                objective_label=objective_label(objective),
                result_label=result_label,
                spend=round(tot_spend, 2),
                budget=round(daily_budget_eur * ((end - start).days + 1), 2),
                impressions=tot_impr,
                link_clicks=tot_clicks,
                cpc=round(tot_spend / tot_clicks, 2) if tot_clicks else 0.0,
                unique_ctr=round(tot_clicks * 0.7 / tot_impr * 100, 2) if tot_impr else 0.0,
                reach=week_reach,
                result=week_result,
                cost_per_result=round(tot_spend / week_result, 2) if week_result else 0.0,
                roas=round(1 + (seed % 50) / 10, 2) if objective in _SALES_OBJECTIVES else None,
                days=days,
            )
        )
    return reports

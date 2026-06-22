import logging
import re
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.orm import Session

from app.core.email import send_email
from app.modules.ads.provider import CampaignReport, get_campaign_reports, sample_campaign_reports
from app.modules.ads.repository import PortfolioRepository
from app.modules.clients.models import Client
from app.modules.clients.repository import ClientRepository
from app.modules.reports.models import EmailTemplate
from app.modules.reports.repository import EmailTemplateRepository
from app.modules.reports.schemas import EmailTemplateSchema
from app.modules.settings.service import resolve_smtp

logger = logging.getLogger("reports")

_env = Environment(
    loader=FileSystemLoader(str(Path(__file__).parent / "templates")),
    autoescape=select_autoescape(["html"]),
)

# Modèle de base par défaut (semé en base au premier accès).
DEFAULT_TEMPLATE = {
    "subject": "Rapport hebdo Meta Ads — {{client}} ({{periode}})",
    "intro": "Bonjour, voici le bilan de vos campagnes Meta Ads sur la semaine écoulée.",
    "closing": "Merci de votre confiance.",
    # Signature libre (saisie par l'agence) — le séparateur « -- » est ajouté au rendu.
    "signature": "",
}

# Placeholders proposés dans l'éditeur (clé -> libellé). Les chiffres = TOTAUX (campagnes gérées).
PLACEHOLDERS = {
    "client": "Nom du client",
    "entreprise": "Entreprise",
    "periode": "Période (du .. au ..)",
    "depenses": "Dépenses (total)",
    "impressions": "Impressions (total)",
    "clics": "Clics (total)",
    "expediteur": "Nom de l'expéditeur",
    "email": "Email de l'expéditeur",
}


def previous_week_range(today: date) -> tuple[date, date]:
    """Semaine complète précédente (lundi → dimanche) par rapport à `today`."""
    last_sunday = today - timedelta(days=today.weekday() + 1)
    last_monday = last_sunday - timedelta(days=6)
    return last_monday, last_sunday


# --- Formats (français : virgule décimale, espace pour les milliers) ---


def _eur(value: float) -> str:
    return f"{value:.2f} €".replace(".", ",")


def _num(value: int) -> str:
    return f"{value:,}".replace(",", " ")


def _pct(value: float) -> str:
    return f"{value:.1f} %".replace(".", ",")


def _plural(n: int, singular: str) -> str:
    """« 1 achat » / « 5 achats » — accord du pluriel (singulier si n < 2)."""
    return f"{_num(n)} {singular if n < 2 else singular + 's'}"


def _placeholder_ctx(
    client_name: str, company: str, totals: tuple[float, int, int], start: date, end: date, sender: tuple[str, str]
) -> dict:
    spend, impressions, clicks = totals
    from_name, from_email = sender
    return {
        "client": client_name,
        "entreprise": company or "",
        "periode": f"du {start:%d/%m/%Y} au {end:%d/%m/%Y}",
        "depenses": _eur(spend),
        "impressions": _num(impressions),
        "clics": _num(clicks),
        "expediteur": from_name or "",
        "email": from_email or "",
    }


def _apply_placeholders(text: str, ctx: dict[str, str]) -> str:
    """Remplace {{ cle }} par sa valeur (laisse tel quel si la clé est inconnue)."""
    return re.sub(r"\{\{\s*(\w+)\s*\}\}", lambda mm: ctx.get(mm.group(1), mm.group(0)), text or "")


# --- Modèles (base + surcharges par client) ---


def get_base(repo: EmailTemplateRepository) -> EmailTemplate:
    """Modèle de base, semé avec les valeurs par défaut au premier accès."""
    base = repo.get_base()
    if base is None:
        base = repo.add(EmailTemplate(client_id=None, **DEFAULT_TEMPLATE))
    return base


def _view(template: EmailTemplate, *, is_override: bool) -> dict:
    return {
        "subject": template.subject,
        "intro": template.intro,
        "closing": template.closing,
        "signature": template.signature or "",
        "is_override": is_override,
    }


def get_base_view(repo: EmailTemplateRepository) -> dict:
    return _view(get_base(repo), is_override=False)


def update_base(repo: EmailTemplateRepository, data: EmailTemplateSchema) -> dict:
    base = get_base(repo)
    base.subject, base.intro, base.closing, base.signature = data.subject, data.intro, data.closing, data.signature
    repo.save(base)
    return _view(base, is_override=False)


def get_client_view(repo: EmailTemplateRepository, client_id: int) -> dict:
    override = repo.get_for_client(client_id)
    if override is not None:
        return _view(override, is_override=True)
    return _view(get_base(repo), is_override=False)


def upsert_override(repo: EmailTemplateRepository, client_id: int, data: EmailTemplateSchema) -> dict:
    override = repo.get_for_client(client_id)
    if override is None:
        override = repo.add(EmailTemplate(client_id=client_id, **data.model_dump()))
    else:
        override.subject, override.intro, override.closing = data.subject, data.intro, data.closing
        override.signature = data.signature
        repo.save(override)
    return _view(override, is_override=True)


def delete_override(repo: EmailTemplateRepository, client_id: int) -> None:
    override = repo.get_for_client(client_id)
    if override is not None:
        repo.delete(override)


def resolve(repo: EmailTemplateRepository, client: Client) -> EmailTemplate:
    """Surcharge du client si elle existe, sinon modèle de base."""
    return repo.get_for_client(client.id) or get_base(repo)


# --- Rendu (email HTML : tout PAR CAMPAGNE — détail par jour + total semaine) ---


def _campaign_view(c: CampaignReport) -> dict:
    """Transforme un CampaignReport en valeurs d'affichage (selon l'objectif)."""
    roas = cost_label = cost_value = None
    if c.objective_label == "Ventes":
        result_col, result_main, show_day = "Achats", _plural(c.result, "achat"), True
        if c.roas:
            roas = f"{c.roas:.1f}".replace(".", ",")
        if c.cost_per_result:
            cost_label, cost_value = "Coût/achat", _eur(c.cost_per_result)
    elif c.objective_label == "Prospects":
        result_col, result_main, show_day = "Leads", _plural(c.result, "lead"), True
        if c.cost_per_result:
            cost_label, cost_value = "Coût/lead", _eur(c.cost_per_result)
    elif c.objective_label == "Notoriété":
        result_col, result_main, show_day = "Portée", f"{_num(c.reach)} de portée", True
    else:  # Trafic / autres : le résultat = les clics -> pas de colonne séparée
        result_col, result_main, show_day = "", _plural(c.link_clicks, "clic"), False

    days = [
        {
            "label": d.label,
            "spend": _eur(d.spend),
            "impressions": _num(d.impressions),
            "clicks": _num(d.link_clicks),
            "ctr": _pct(d.ctr),
            "result": _num(d.result) if show_day else "",
        }
        for d in c.days
    ]
    return {
        "name": c.name,
        "objective": c.objective_label,
        "result_col": result_col,
        "result_main": result_main,
        "result_total": _num(c.result) if show_day else "",
        "cost_label": cost_label,
        "cost_value": cost_value,
        "roas": roas,
        "spend": _eur(c.spend),
        "budget": _eur(c.budget) if c.budget is not None else None,
        "impressions": _num(c.impressions),
        "clicks": _num(c.link_clicks),
        "cpc": _eur(c.cpc),
        "unique_ctr": _pct(c.unique_ctr),
        "days": days,
    }


def _render(
    client, tpl, reports: list[CampaignReport], start: date, end: date, sender: tuple[str, str] = ("", "")
) -> tuple[str, str]:
    """tpl = EmailTemplate (envoi réel) ou dict (aperçu d'un modèle non enregistré)."""
    subject_t = tpl["subject"] if isinstance(tpl, dict) else tpl.subject
    intro_t = tpl["intro"] if isinstance(tpl, dict) else tpl.intro
    closing_t = tpl["closing"] if isinstance(tpl, dict) else tpl.closing
    signature_t = (tpl.get("signature") if isinstance(tpl, dict) else getattr(tpl, "signature", "")) or ""
    totals = (
        round(sum(c.spend for c in reports), 2),
        sum(c.impressions for c in reports),
        sum(c.link_clicks for c in reports),
    )
    ctx = _placeholder_ctx(client.name, getattr(client, "company", "") or "", totals, start, end, sender)
    html = _env.get_template("weekly_report.html").render(
        client=client.name,
        periode=ctx["periode"],
        intro=_apply_placeholders(intro_t, ctx),
        closing=_apply_placeholders(closing_t, ctx),
        signature=_apply_placeholders(signature_t, ctx),
        totals={"depenses": ctx["depenses"], "impressions": ctx["impressions"], "clics": ctx["clics"]},
        campaigns=[_campaign_view(c) for c in reports],
    )
    return html, _apply_placeholders(subject_t, ctx)


def _managed_reports(db: Session, client: Client, start: date, end: date) -> list[CampaignReport]:
    """Rapports des campagnes GÉRÉES (allowlist) du portefeuille du client."""
    managed = set(client.managed_campaign_ids or [])
    out: list[CampaignReport] = []
    if client.meta_business_id and managed:
        for account in PortfolioRepository(db).accounts_for_business(client.meta_business_id):
            out.extend(r for r in get_campaign_reports(account.id, start, end) if r.id in managed)
    return out


def _sender(db: Session) -> tuple[str, str]:
    """(nom, email) de l'expéditeur depuis la config SMTP — variables {{expediteur}} / {{email}}."""
    cfg = resolve_smtp(db)
    return (cfg.from_name or "", cfg.from_email or "")


def _report(db: Session, client: Client, today: date | None = None) -> tuple[str, str, date, date]:
    today = today or date.today()
    start, end = previous_week_range(today)
    tpl = resolve(EmailTemplateRepository(db), client)
    reports = _managed_reports(db, client, start, end)
    html, subject = _render(client, tpl, reports, start, end, _sender(db))
    return html, subject, start, end


def preview_report(db: Session, client: Client, today: date | None = None) -> dict:
    """Aperçu du rapport (modèle résolu + campagnes gérées + vraies données Meta), sans envoi."""
    html, subject, start, end = _report(db, client, today)
    return {"html": html, "subject": subject, "start": start.isoformat(), "end": end.isoformat()}


def preview_template(
    db: Session, client: Client | None, data: EmailTemplateSchema, today: date | None = None
) -> dict:
    """Aperçu en direct d'un modèle (même non enregistré) avec données d'EXEMPLE (sans appel Meta)."""
    today = today or date.today()
    start, end = previous_week_range(today)
    sample_client = client or SimpleNamespace(name="Client Exemple", company="Entreprise Exemple")
    reports = sample_campaign_reports(start, end)
    html, subject = _render(sample_client, data.model_dump(), reports, start, end, _sender(db))
    return {"html": html, "subject": subject}


def send_report_for_client(
    db: Session, client: Client, today: date | None = None, to: list[str] | None = None
) -> list[str] | None:
    """Construit le rapport (modèle résolu + campagnes gérées) et l'envoie aux emails choisis."""
    recipients = [r for r in (to if to else (client.emails or [])) if r]
    if not recipients:
        logger.warning("Client %s (%s) sans email — rapport non envoyé", client.id, client.name)
        return None
    html, subject, _start, _end = _report(db, client, today)
    send_email(recipients, subject, html)
    ClientRepository(db).mark_report_sent(client)
    return recipients


def send_weekly_reports_for_day(db: Session, day: int, today: date | None = None) -> dict[str, int]:
    """Envoie le rapport à tous les clients actifs dont le jour d'envoi vaut `day`.

    Renvoie le détail réel : `{sent, failed, total}` — un échec SMTP ou un client sans
    email destinataire compte comme `failed` (l'envoi groupé ne doit pas annoncer un faux succès).
    """
    clients = ClientRepository(db).list_active_by_day(day)
    sent = failed = 0
    for client in clients:
        try:
            if send_report_for_client(db, client, today=today):
                sent += 1
            else:
                failed += 1  # pas d'email destinataire → rien envoyé
        except Exception:
            failed += 1
            logger.exception("Échec de l'envoi du rapport au client %s (%s)", client.id, client.name)
    return {"sent": sent, "failed": failed, "total": len(clients)}

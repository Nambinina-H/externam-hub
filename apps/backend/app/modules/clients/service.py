import csv
import io
import re
import unicodedata
from collections import Counter

from app.core.errors import NotFoundError
from app.shared.pagination import Page, PaginationParams
from app.modules.clients.models import Client
from app.modules.clients.repository import ClientRepository
from app.modules.clients.schemas import (
    ClientCreateSchema,
    ClientPublicSchema,
    ClientUpdateSchema,
    ImportMapping,
)

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


def list_clients(repo: ClientRepository, params: PaginationParams) -> Page[ClientPublicSchema]:
    items, total = repo.list_paginated(params)
    return Page[ClientPublicSchema](
        items=[ClientPublicSchema.model_validate(client) for client in items],
        total=total,
        page=params.page,
        size=params.size,
    )


def get_client(repo: ClientRepository, client_id: int) -> Client:
    client = repo.get_by_id(client_id)
    if not client:
        raise NotFoundError("Client introuvable")
    return client


def create_client(repo: ClientRepository, data: ClientCreateSchema) -> ClientPublicSchema:
    client = Client(
        name=data.name,
        company=data.company,
        contact_name=data.contact_name,
        phone=data.phone,
        emails=[str(email) for email in data.emails],
        meta_business_id=data.meta_business_id,
        meta_ad_account_id=data.meta_ad_account_id,
        report_day=int(data.report_day),
        is_active=data.is_active,
    )
    created = repo.create(client)
    return ClientPublicSchema.model_validate(created)


def update_client(repo: ClientRepository, client_id: int, data: ClientUpdateSchema) -> ClientPublicSchema:
    client = get_client(repo, client_id)
    fields = data.model_dump(exclude_unset=True)
    if "report_day" in fields and fields["report_day"] is not None:
        fields["report_day"] = int(fields["report_day"])
    if "emails" in fields and fields["emails"] is not None:
        fields["emails"] = [str(email) for email in fields["emails"]]
    for key, value in fields.items():
        setattr(client, key, value)
    saved = repo.save(client)
    return ClientPublicSchema.model_validate(saved)


def delete_client(repo: ClientRepository, client_id: int) -> None:
    client = get_client(repo, client_id)
    repo.delete(client)


# --- Import CSV ---


def _parse_csv(text: str) -> tuple[list[str], list[dict]]:
    """Parse robuste (gère les guillemets et les sauts de ligne dans les cellules)."""
    reader = csv.DictReader(io.StringIO(text))
    headers = list(reader.fieldnames or [])
    rows = [dict(row) for row in reader]
    return headers, rows


def _extract_emails(value: str | None) -> list[str]:
    """Extrait tous les emails d'une cellule (multiples, format <…>, ignore le reste)."""
    if not value:
        return []
    return list(dict.fromkeys(_EMAIL_RE.findall(value)))


def _cell(row: dict, header: str | None) -> str:
    return (row.get(header) or "").strip() if header else ""


def preview_import(csv_text: str) -> dict:
    headers, rows = _parse_csv(csv_text)
    return {"headers": headers, "sample": rows[:5], "count": len(rows)}


def import_clients(repo: ClientRepository, csv_text: str, mapping: ImportMapping) -> dict:
    """Upsert : crée les nouveaux clients, met à jour ceux qui existent déjà (même nom).

    On ne met à jour que les champs fournis et non vides (on n'écrase pas une valeur
    existante par une cellule vide). Les lignes sans nom sont ignorées.
    """
    _headers, rows = _parse_csv(csv_text)
    by_name = {client.name.lower(): client for client in repo.list_all()}
    created = updated = skipped = 0
    for row in rows:
        name = _cell(row, mapping.name)
        if not name:
            skipped += 1
            continue
        company = _cell(row, mapping.company) or None
        contact_name = _cell(row, mapping.contact_name) or None
        phone = _cell(row, mapping.phone) or None
        emails = _extract_emails(row.get(mapping.emails) if mapping.emails else None)

        existing = by_name.get(name.lower())
        if existing is not None:
            if company:
                existing.company = company
            if contact_name:
                existing.contact_name = contact_name
            if phone:
                existing.phone = phone
            if emails:
                existing.emails = emails
            repo.save(existing)
            updated += 1
        else:
            client = Client(
                name=name,
                company=company,
                contact_name=contact_name,
                phone=phone,
                emails=emails,
                report_day=0,
                is_active=True,
            )
            by_name[name.lower()] = repo.create(client)
            created += 1
    return {"created": created, "updated": updated, "skipped": skipped}


# --- Liaison automatique aux portefeuilles business (par cohérence) ---

# Fournisseurs d'emails génériques : leur domaine n'identifie pas un client.
_FREEMAIL = {
    "gmail", "googlemail", "outlook", "hotmail", "live", "msn", "yahoo", "ymail",
    "icloud", "me", "mac", "aol", "gmx", "proton", "protonmail", "pm",
    "orange", "wanadoo", "free", "sfr", "neuf", "laposte", "bbox", "numericable",
}
# Mots structurels sans valeur discriminante.
_STOPWORDS = {"des", "les", "sarl", "sas", "eurl", "inc", "ltd", "pub", "ads", "spa"}


def _norm(value: str | None) -> str:
    if not value:
        return ""
    return unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()


def _slug(value: str | None) -> str:
    """Alphanumérique compact (sans accents, espaces ni ponctuation)."""
    return re.sub(r"[^a-z0-9]", "", _norm(value))


def _tokens(value: str | None) -> set[str]:
    """Mots significatifs (>= 3 lettres, hors mots structurels)."""
    return {t for t in re.split(r"[^a-z0-9]+", _norm(value)) if len(t) >= 3 and t not in _STOPWORDS}


def _email_domain_root(email: str) -> str | None:
    """Racine du domaine email (ex. best-energy-control), ou None si fournisseur générique."""
    if "@" not in email:
        return None
    root = email.split("@", 1)[1].split(".")[0]
    return None if root in _FREEMAIL else root


def auto_link_clients(repo: ClientRepository, portfolios: list[dict]) -> int:
    """Lie chaque client NON lié au portefeuille qui correspond *vraiment*, sinon le laisse libre.

    Stratégie prudente (ne pas inventer) :
    - tokens discriminants partagés (rares parmi les portefeuilles), pondérés par leur rareté ;
    - bonus si un libellé du client est contenu dans le NOM d'UN SEUL portefeuille ;
    - les fournisseurs d'emails génériques (gmail…) sont ignorés ;
    - on ne lie que si un portefeuille ressort nettement (meilleur score, sans ex-aequo).
    """
    ports = []
    for p in portfolios:
        if not p.get("id"):
            continue
        tokens = set(_tokens(p.get("name")))
        for account in p.get("accounts", []):
            tokens |= _tokens(account.get("name"))
        ports.append({"id": p["id"], "name_slug": _slug(p.get("name")), "tokens": tokens})

    if not ports:
        return 0

    df: Counter[str] = Counter()
    for p in ports:
        df.update(p["tokens"])
    max_df = max(2, len(ports) // 6)  # au-delà : token trop commun => non discriminant

    linked = 0
    for client in repo.list_all():
        if client.meta_business_id:
            continue  # on ne touche pas aux liaisons existantes

        client_tokens = _tokens(client.name) | _tokens(client.company)
        client_slugs = {s for s in (_slug(client.name), _slug(client.company)) if len(s) >= 5}
        for email in client.emails or []:
            root = _email_domain_root(email)
            if root:
                client_tokens |= _tokens(root)
                if len(_slug(root)) >= 5:
                    client_slugs.add(_slug(root))

        # Containment : un slug du client contenu dans le nom d'UN SEUL portefeuille.
        bonus: dict[str, float] = {}
        for slug in client_slugs:
            hits = [p["id"] for p in ports if slug in p["name_slug"] or p["name_slug"] in slug]
            if len(hits) == 1:
                bonus[hits[0]] = 3.0

        scores: dict[str, float] = {}
        for p in ports:
            score = sum(1.0 / df[t] for t in (client_tokens & p["tokens"]) if df[t] <= max_df)
            score += bonus.get(p["id"], 0.0)
            if score > 0:
                scores[p["id"]] = score

        if not scores:
            continue
        best_id = max(scores, key=scores.get)
        best = scores[best_id]
        # Lien uniquement si suffisamment fort ET sans ex-aequo (sinon on n'invente pas).
        if best >= 1.0 and sum(1 for v in scores.values() if abs(v - best) < 1e-9) == 1:
            client.meta_business_id = best_id
            repo.save(client)
            linked += 1
    return linked

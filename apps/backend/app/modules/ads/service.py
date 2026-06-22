"""Persistance des portefeuilles/comptes Meta.

- `list_portfolios` : lit la base (rapide, aucun appel Meta).
- `sync_portfolios` : tire l'état frais depuis Meta et fait un **upsert + soft-remove**
  (insertion des nouveaux, mise à jour des existants, marquage `removed_at` des disparus).
"""

from datetime import datetime, timezone

from app.modules.ads.models import MetaAdAccount, MetaPortfolio
from app.modules.ads.repository import PortfolioRepository

# Clé interne pour les comptes sans portefeuille (Meta renvoie business=None).
_UNLINKED = "_none"


def list_portfolios(repo: PortfolioRepository) -> dict:
    """Vue : portefeuilles actifs + leurs comptes actifs, regroupés (même forme que l'API Meta)."""
    accounts_by_business: dict[str, list[dict]] = {}
    for account in repo.active_accounts():
        accounts_by_business.setdefault(account.business_id, []).append(
            {
                "id": account.id,
                "account_id": account.account_id,
                "name": account.name,
                "currency": account.currency,
                "account_status": account.account_status,
            }
        )

    portfolios = [
        {
            "id": None if portfolio.business_id == _UNLINKED else portfolio.business_id,
            "name": portfolio.name,
            "accounts": accounts_by_business.get(portfolio.business_id, []),
        }
        for portfolio in repo.active_portfolios()
    ]
    return {"portfolios": portfolios, "last_synced_at": repo.last_synced_at()}


def sync_portfolios(repo: PortfolioRepository, client, source_business_id: str | None) -> dict:
    """Synchronise la base avec Meta. Idempotent : insère/maj les présents, marque retirés les absents."""
    groups = client.list_portfolios(source_business_id)  # appel Meta (live)
    now = datetime.now(timezone.utc)

    portfolios = {p.business_id: p for p in repo.all_portfolios()}
    accounts = {a.id: a for a in repo.all_accounts()}
    seen_portfolios: set[str] = set()
    seen_accounts: set[str] = set()
    p_created = p_updated = a_created = a_updated = 0

    # 1) Portefeuilles d'abord : les comptes les référencent via clé étrangère.
    for group in groups:
        business_id = group.get("id") or _UNLINKED
        name = group.get("name") or "(non rattaché à un portefeuille)"
        seen_portfolios.add(business_id)

        portfolio = portfolios.get(business_id)
        if portfolio is None:
            portfolio = MetaPortfolio(business_id=business_id, name=name, last_synced_at=now, removed_at=None)
            repo.add(portfolio)
            portfolios[business_id] = portfolio
            p_created += 1
        else:
            portfolio.name = name
            portfolio.last_synced_at = now
            portfolio.removed_at = None
            p_updated += 1

    # Insère les portefeuilles AVANT les comptes (sinon ForeignKeyViolation sur Postgres,
    # où les FK sont appliquées — contrairement à SQLite qui les ignore par défaut).
    repo.flush()

    # 2) Comptes ensuite.
    for group in groups:
        business_id = group.get("id") or _UNLINKED
        for raw in group.get("accounts") or []:
            account_id = raw.get("id")
            if not account_id:
                continue
            seen_accounts.add(account_id)

            account = accounts.get(account_id)
            if account is None:
                account = MetaAdAccount(
                    id=account_id,
                    account_id=raw.get("account_id"),
                    name=raw.get("name"),
                    currency=raw.get("currency"),
                    account_status=raw.get("account_status"),
                    business_id=business_id,
                    last_synced_at=now,
                    removed_at=None,
                )
                repo.add(account)
                accounts[account_id] = account
                a_created += 1
            else:
                account.account_id = raw.get("account_id")
                account.name = raw.get("name")
                account.currency = raw.get("currency")
                account.account_status = raw.get("account_status")
                account.business_id = business_id
                account.last_synced_at = now
                account.removed_at = None
                a_updated += 1

    # Soft-remove : présents en base mais absents du dernier fetch.
    p_removed = sum(
        1
        for business_id, portfolio in portfolios.items()
        if business_id not in seen_portfolios and portfolio.removed_at is None and _mark_removed(portfolio, now)
    )
    a_removed = sum(
        1
        for account_id, account in accounts.items()
        if account_id not in seen_accounts and account.removed_at is None and _mark_removed(account, now)
    )

    repo.commit()
    return {
        "portfolios": {"created": p_created, "updated": p_updated, "removed": p_removed},
        "accounts": {"created": a_created, "updated": a_updated, "removed": a_removed},
        "synced_at": now,
    }


def _mark_removed(obj, now: datetime) -> bool:
    obj.removed_at = now
    return True

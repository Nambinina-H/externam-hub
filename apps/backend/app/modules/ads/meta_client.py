"""Client (sync) pour la Meta Marketing API — Graph API v25.0.

Lecture seule : businesses -> ad accounts -> campaigns -> insights.
- Token via header `Authorization: Bearer ...` (hors URL/logs).
- Pagination par curseur (suit `paging.cursors.after` tant que `paging.next` existe).
- Retry/backoff sur rate-limit + 5xx ; erreurs typées (auth vs rate-limit).
- Conçu pour un System User token (cf. config META_ACCESS_TOKEN).

Conçu pour rester testable : injecter un `httpx.Client` (ex. MockTransport) via `client=`.
"""

import hashlib
import hmac
import json
import logging
import time
from datetime import date

import httpx

logger = logging.getLogger("meta_ads")

# Codes d'erreur Meta : auth/permission (non-retryable) vs rate-limit (retryable).
_AUTH_CODES = {190, 102, 10, 200, 803}
_RATE_LIMIT_CODES = {4, 17, 32, 613, 80000, 80003, 80004, 80014}

DEFAULT_INSIGHTS_FIELDS = ("spend", "impressions", "clicks", "ctr", "cpc", "actions")


class MetaApiError(Exception):
    def __init__(self, message, *, code=None, subcode=None, type=None, fbtrace_id=None, http_status=None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.subcode = subcode
        self.type = type
        self.fbtrace_id = fbtrace_id
        self.http_status = http_status


class MetaAuthError(MetaApiError):
    """Token invalide/expiré ou permission manquante — erreur de config, non-retryable."""


class MetaRateLimitError(MetaApiError):
    def __init__(self, message, *, retry_after=60.0, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


def _act(account_id: str) -> str:
    """Normalise un id de compte en `act_<num>`."""
    account_id = str(account_id)
    return account_id if account_id.startswith("act_") else f"act_{account_id}"


def _day(value) -> str:
    return value.isoformat() if isinstance(value, date) else str(value)


class MetaAdsClient:
    def __init__(
        self,
        access_token,
        *,
        version="v25.0",
        app_secret=None,
        timeout=30.0,
        max_retries=5,
        client=None,
    ):
        self.access_token = access_token
        self.app_secret = app_secret
        self.max_retries = max_retries
        self._owns_client = client is None
        self._client = client or httpx.Client(
            base_url=f"https://graph.facebook.com/{version}",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=timeout,
        )

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        self.close()

    def close(self):
        if self._owns_client:
            self._client.close()

    # ---- HTTP bas niveau -------------------------------------------------

    def _appsecret_proof(self):
        if not self.app_secret:
            return None
        return hmac.new(self.app_secret.encode(), self.access_token.encode(), hashlib.sha256).hexdigest()

    def _get(self, path, params):
        params = {k: v for k, v in (params or {}).items() if v is not None}
        proof = self._appsecret_proof()
        if proof:
            params["appsecret_proof"] = proof

        attempt = 0
        while True:
            attempt += 1
            try:
                resp = self._client.get(path, params=params)
            except httpx.RequestError as exc:
                if attempt <= self.max_retries:
                    time.sleep(min(2**attempt, 60))
                    continue
                raise MetaApiError(f"Erreur réseau Meta : {exc}") from exc

            self._log_usage(resp)
            data = self._parse(resp)

            if "error" in data:
                exc = self._build_error(data["error"], resp.status_code)
                if isinstance(exc, MetaRateLimitError) and attempt <= self.max_retries:
                    logger.warning("Meta rate-limit (code %s) — retry %d dans %.0fs", exc.code, attempt, exc.retry_after)
                    time.sleep(exc.retry_after)
                    continue
                if resp.status_code >= 500 and attempt <= self.max_retries:
                    time.sleep(min(2**attempt, 60))
                    continue
                raise exc
            return data

    def _parse(self, resp):
        try:
            return resp.json()
        except (json.JSONDecodeError, ValueError) as exc:
            if resp.status_code >= 400:
                raise MetaApiError(
                    f"Réponse Meta non-JSON (HTTP {resp.status_code})", http_status=resp.status_code
                ) from exc
            return {}

    def _build_error(self, err, http_status):
        code = err.get("code")
        kwargs = dict(
            code=code,
            subcode=err.get("error_subcode"),
            type=err.get("type"),
            fbtrace_id=err.get("fbtrace_id"),
            http_status=http_status,
        )
        message = err.get("message", "Erreur Meta API")
        if code in _RATE_LIMIT_CODES or http_status == 429:
            return MetaRateLimitError(message, retry_after=60.0, **kwargs)
        if code in _AUTH_CODES:
            return MetaAuthError(message, **kwargs)
        return MetaApiError(message, **kwargs)

    def _log_usage(self, resp):
        for header in ("x-app-usage", "x-business-use-case-usage", "x-ad-account-usage"):
            value = resp.headers.get(header)
            if value:
                logger.debug("Meta usage %s: %s", header, value)

    def _paginate(self, path, params):
        params = dict(params or {})
        while True:
            data = self._get(path, params)
            yield from data.get("data", [])
            paging = data.get("paging") or {}
            after = (paging.get("cursors") or {}).get("after")
            if not paging.get("next") or not after:
                break
            params["after"] = after

    # ---- API publique ----------------------------------------------------

    def list_businesses(self):
        return list(self._paginate("/me/businesses", {"fields": "id,name,verification_status", "limit": 50}))

    def list_ad_accounts(self, business_id=None):
        fields = "id,account_id,name,account_status,currency,timezone_name,business{id,name}"
        if business_id is None:
            return list(self._paginate("/me/adaccounts", {"fields": fields, "limit": 100}))
        owned = self._paginate(f"/{business_id}/owned_ad_accounts", {"fields": fields, "limit": 100})
        client = self._paginate(f"/{business_id}/client_ad_accounts", {"fields": fields, "limit": 100})
        return [*owned, *client]

    def accessible_accounts(self, source_business_id=None):
        """Comptes accessibles, dédupliqués par id :
        - ceux affectés à l'utilisateur système (`/me/adaccounts`) ;
        - si `source_business_id` est fourni, AUSSI ceux partagés avec ce business
          (owned + client_ad_accounts) — i.e. un simple partage de portefeuille suffit,
          sans avoir à réaffecter chaque compte à l'utilisateur système.
        """
        seen: dict[str, dict] = {}
        for account in self.list_ad_accounts():
            if account.get("id"):
                seen.setdefault(account["id"], account)
        if source_business_id:
            for account in self.list_ad_accounts(source_business_id):
                if account.get("id"):
                    seen.setdefault(account["id"], account)
        return list(seen.values())

    def list_portfolios(self, source_business_id=None):
        """Comptes accessibles regroupés par portefeuille (business) propriétaire.

        Renvoie [{id, name, accounts: [{id, account_id, name, currency, account_status}]}].
        Permet de vérifier l'appartenance (un portefeuille = un client, possiblement plusieurs comptes).
        """
        groups: dict[str, dict] = {}
        for account in self.accessible_accounts(source_business_id):
            business = account.get("business") or {}
            key = business.get("id") or "_none"
            if key not in groups:
                groups[key] = {
                    "id": business.get("id"),
                    "name": business.get("name") or "(non rattaché à un portefeuille)",
                    "accounts": [],
                }
            groups[key]["accounts"].append(
                {
                    "id": account.get("id"),
                    "account_id": account.get("account_id"),
                    "name": account.get("name"),
                    "currency": account.get("currency"),
                    "account_status": account.get("account_status"),
                }
            )
        return sorted(groups.values(), key=lambda g: (g["name"] or "").lower())

    def accounts_in_business(self, owner_business_id, source_business_id=None):
        """Ids des comptes pub (act_…) dont le portefeuille PROPRIÉTAIRE est `owner_business_id`.

        `source_business_id` (optionnel) élargit la découverte aux comptes partagés avec le
        business partenaire (cf. `accessible_accounts`), pour les portefeuilles non affectés
        directement à l'utilisateur système.
        """
        return [
            account["id"]
            for account in self.accessible_accounts(source_business_id)
            if (account.get("business") or {}).get("id") == str(owner_business_id) and account.get("id")
        ]

    def list_campaigns(self, account_id, effective_status=None):
        params = {
            "fields": "id,name,status,effective_status,objective,daily_budget,lifetime_budget,start_time,stop_time",
            "limit": 100,
        }
        if effective_status:
            params["effective_status"] = json.dumps(list(effective_status))
        return list(self._paginate(f"/{_act(account_id)}/campaigns", params))

    def get_insights(
        self, account_id, since, until, *, level="account", time_increment=None, fields=None,
        action_attribution_windows=None,
    ):
        """Insights agrégés/temporels. time_increment=1 -> série quotidienne ; None -> agrégat période.

        `action_attribution_windows` (ex. ['7d_click']) aligne le comptage des résultats sur Ads Manager.
        """
        params = {
            "level": level,
            "fields": ",".join(fields or DEFAULT_INSIGHTS_FIELDS),
            "time_range": json.dumps({"since": _day(since), "until": _day(until)}),
            "limit": 500,
        }
        if time_increment is not None:
            params["time_increment"] = time_increment
        if action_attribution_windows:
            params["action_attribution_windows"] = json.dumps(list(action_attribution_windows))
        return list(self._paginate(f"/{_act(account_id)}/insights", params))

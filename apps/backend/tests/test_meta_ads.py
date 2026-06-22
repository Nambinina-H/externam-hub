import time
from datetime import date
from types import SimpleNamespace

import httpx
import pytest

from app.modules.ads.meta_client import MetaAdsClient, MetaApiError, MetaAuthError

BASE = "https://graph.facebook.com/v25.0"


def _client(handler):
    """MetaAdsClient avec un httpx.Client mocké (MockTransport)."""
    return MetaAdsClient("TESTTOKEN", client=httpx.Client(base_url=BASE, transport=httpx.MockTransport(handler)))


def test_pagination_follows_cursor():
    def handler(request):
        after = request.url.params.get("after")
        if after is None:
            return httpx.Response(
                200,
                json={
                    "data": [{"id": "1"}, {"id": "2"}],
                    "paging": {"cursors": {"after": "C1"}, "next": f"{BASE}/act_1/campaigns?after=C1"},
                },
            )
        return httpx.Response(200, json={"data": [{"id": "3"}]})

    with _client(handler) as client:
        rows = client.list_campaigns("act_1")
    assert [r["id"] for r in rows] == ["1", "2", "3"]


def test_auth_error_maps_190():
    def handler(_request):
        return httpx.Response(400, json={"error": {"message": "Invalid OAuth token", "code": 190}})

    with _client(handler) as client:
        with pytest.raises(MetaAuthError):
            client.list_businesses()


def test_rate_limit_retries(monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda *a, **k: None)
    state = {"n": 0}

    def handler(_request):
        state["n"] += 1
        if state["n"] == 1:
            return httpx.Response(400, json={"error": {"message": "rate limit", "code": 613}})
        return httpx.Response(200, json={"data": [{"id": "biz"}]})

    with _client(handler) as client:
        rows = client.list_businesses()
    assert state["n"] == 2
    assert rows == [{"id": "biz"}]


def test_non_retryable_error_raises():
    def handler(_request):
        return httpx.Response(400, json={"error": {"message": "boom", "code": 100}})

    with _client(handler) as client:
        with pytest.raises(MetaApiError):
            client.list_businesses()


def test_act_prefix_normalised():
    seen = {}

    def handler(request):
        seen["path"] = request.url.path
        return httpx.Response(200, json={"data": []})

    with _client(handler) as client:
        client.list_campaigns("123456")  # sans préfixe
    assert seen["path"].endswith("/act_123456/campaigns")


def test_provider_stub_without_token():
    from app.modules.ads.provider import _stub_weekly_metrics, get_weekly_metrics

    start, end = date(2026, 6, 8), date(2026, 6, 14)
    # En env test, META_ACCESS_TOKEN n'est pas défini -> fallback stub déterministe.
    assert get_weekly_metrics("act_5", start, end) == _stub_weekly_metrics("act_5", start, end)


def test_provider_parses_real_insights(monkeypatch):
    fake_settings = SimpleNamespace(
        meta_access_token="X",
        meta_graph_version="v25.0",
        meta_app_secret="",
        meta_api_timeout=30.0,
        meta_max_retries=5,
    )
    monkeypatch.setattr("app.modules.ads.provider.get_settings", lambda: fake_settings)

    canned = [
        {
            "spend": "123.45",
            "impressions": "10000",
            "clicks": "250",
            "ctr": "2.5",
            "cpc": "0.49",
            "actions": [
                {"action_type": "purchase", "value": "12"},
                {"action_type": "lead", "value": "3"},
                {"action_type": "link_click", "value": "250"},
            ],
        }
    ]

    class FakeClient:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def get_insights(self, *a, **k):
            return canned

    monkeypatch.setattr("app.modules.ads.meta_client.MetaAdsClient", FakeClient)

    from app.modules.ads.provider import get_weekly_metrics

    m = get_weekly_metrics("act_999", date(2026, 6, 8), date(2026, 6, 14))  # objectif par défaut "purchase"
    assert m.spend == 123.45
    assert m.impressions == 10000
    assert m.clicks == 250
    assert m.conversions == 12  # objectif "purchase" -> 12 (lead/link_click non comptés)
    assert m.ctr == 2.5
    assert m.cpc == 0.49

    # Même data, autre objectif -> autre comptage.
    m_lead = get_weekly_metrics("act_999", date(2026, 6, 8), date(2026, 6, 14), conversion_goal="lead")
    assert m_lead.conversions == 3


def test_list_portfolios_groups_by_business():
    def handler(_request):
        return httpx.Response(
            200,
            json={
                "data": [
                    {"id": "act_1", "account_id": "1", "name": "Acc1", "currency": "EUR",
                     "business": {"id": "biz_A", "name": "Portfolio A"}},
                    {"id": "act_2", "account_id": "2", "name": "Acc2", "currency": "EUR",
                     "business": {"id": "biz_A", "name": "Portfolio A"}},
                    {"id": "act_3", "account_id": "3", "name": "Acc3", "currency": "USD",
                     "business": {"id": "biz_B", "name": "Portfolio B"}},
                ]
            },
        )

    with _client(handler) as client:
        portfolios = client.list_portfolios()

    by_name = {p["name"]: p for p in portfolios}
    assert len(portfolios) == 2
    assert len(by_name["Portfolio A"]["accounts"]) == 2
    assert len(by_name["Portfolio B"]["accounts"]) == 1


def test_business_weekly_metrics_aggregates(monkeypatch):
    fake_settings = SimpleNamespace(
        meta_access_token="X",
        meta_graph_version="v25.0",
        meta_app_secret="",
        meta_api_timeout=30.0,
        meta_max_retries=5,
        meta_business_id="",
    )
    monkeypatch.setattr("app.modules.ads.provider.get_settings", lambda: fake_settings)

    insights = {
        "act_1": [{"spend": "100", "impressions": "1000", "clicks": "50",
                   "actions": [{"action_type": "purchase", "value": "5"}]}],
        "act_2": [{"spend": "50", "impressions": "500", "clicks": "20",
                   "actions": [{"action_type": "purchase", "value": "3"}]}],
    }

    class FakeClient:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def accounts_in_business(self, _business_id, _source_business_id=None):
            return ["act_1", "act_2"]

        def get_insights(self, account_id, **_k):
            return insights.get(account_id, [])

    monkeypatch.setattr("app.modules.ads.meta_client.MetaAdsClient", FakeClient)

    from app.modules.ads.provider import get_business_weekly_metrics

    m = get_business_weekly_metrics("biz_1", date(2026, 6, 8), date(2026, 6, 14), "purchase")
    assert m.spend == 150.0  # 100 + 50
    assert m.impressions == 1500  # 1000 + 500
    assert m.clicks == 70  # 50 + 20
    assert m.conversions == 8  # 5 + 3
    assert m.ctr == round(70 / 1500 * 100, 2)
    assert m.cpc == round(150 / 70, 2)


# --- Étape 1 : liste des campagnes -----------------------------------------


def test_account_campaigns_stub_without_token():
    from app.modules.ads.provider import get_account_campaigns

    # En env test : pas de token -> campagnes fictives, non vides et déterministes.
    campaigns = get_account_campaigns("act_42")
    assert campaigns
    assert get_account_campaigns("act_42") == campaigns
    assert {"id", "name", "objective", "objective_label", "status", "effective_status"} <= campaigns[0].keys()
    # Aucun libellé brut (toujours traduit).
    assert all(not (c["objective_label"] or "").startswith("OUTCOME_") for c in campaigns)


def test_objective_label_maps_recent_and_legacy():
    from app.modules.ads.provider import objective_label

    assert objective_label("OUTCOME_SALES") == "Ventes"
    assert objective_label("CONVERSIONS") == "Ventes"  # ancien objectif
    assert objective_label("OUTCOME_LEADS") == "Prospects"
    assert objective_label(None) == "—"
    assert objective_label("SOME_UNKNOWN") == "Some Unknown"  # repli lisible


def test_account_campaigns_real_path(monkeypatch):
    fake_settings = SimpleNamespace(
        meta_access_token="X",
        meta_graph_version="v25.0",
        meta_app_secret="",
        meta_api_timeout=30.0,
        meta_max_retries=5,
    )
    monkeypatch.setattr("app.modules.ads.provider.get_settings", lambda: fake_settings)

    class FakeClient:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def list_campaigns(self, _account_id):
            return [
                {"id": "c1", "name": "Soldes", "objective": "OUTCOME_SALES", "status": "ACTIVE",
                 "effective_status": "ACTIVE"},
            ]

    monkeypatch.setattr("app.modules.ads.meta_client.MetaAdsClient", FakeClient)

    from app.modules.ads.provider import get_account_campaigns

    assert get_account_campaigns("act_999") == [
        {"id": "c1", "name": "Soldes", "objective": "OUTCOME_SALES", "objective_label": "Ventes",
         "status": "ACTIVE", "effective_status": "ACTIVE"},
    ]

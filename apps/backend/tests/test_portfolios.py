"""Synchronisation des portefeuilles Meta : upsert + soft-remove, lecture base."""

from app.modules.ads import service
from app.modules.ads.repository import PortfolioRepository


class FakeMetaClient:
    """Renvoie des portefeuilles canned (aucun appel réseau)."""

    def __init__(self, groups):
        self._groups = groups

    def list_portfolios(self, _source_business_id=None):
        return self._groups


_RUN1 = [
    {
        "id": "biz_A",
        "name": "Portfolio A",
        "accounts": [
            {"id": "act_1", "account_id": "1", "name": "Acc1", "currency": "EUR", "account_status": 1},
            {"id": "act_2", "account_id": "2", "name": "Acc2", "currency": "EUR", "account_status": 1},
        ],
    },
    {
        "id": "biz_B",
        "name": "Portfolio B",
        "accounts": [{"id": "act_3", "account_id": "3", "name": "Acc3", "currency": "USD", "account_status": 1}],
    },
]


def test_sync_creates_then_reads_from_db(db_session):
    repo = PortfolioRepository(db_session)

    result = service.sync_portfolios(repo, FakeMetaClient(_RUN1), None)
    assert result["portfolios"]["created"] == 2
    assert result["accounts"]["created"] == 3
    assert result["portfolios"]["removed"] == 0

    view = service.list_portfolios(repo)
    assert len(view["portfolios"]) == 2
    assert view["last_synced_at"] is not None
    by_name = {p["name"]: p for p in view["portfolios"]}
    assert len(by_name["Portfolio A"]["accounts"]) == 2
    # Un portefeuille non rattaché à un client est exposé avec id = business_id réel.
    assert by_name["Portfolio A"]["id"] == "biz_A"


def test_sync_upsert_and_soft_remove(db_session):
    repo = PortfolioRepository(db_session)
    service.sync_portfolios(repo, FakeMetaClient(_RUN1), None)

    # 2e synchro : biz_B disparaît, Acc1 renommé, nouveau act_4 ; act_2 et act_3 disparaissent.
    run2 = [
        {
            "id": "biz_A",
            "name": "Portfolio A",
            "accounts": [
                {"id": "act_1", "account_id": "1", "name": "Acc1 renommé", "currency": "EUR", "account_status": 1},
                {"id": "act_4", "account_id": "4", "name": "Acc4", "currency": "EUR", "account_status": 1},
            ],
        }
    ]
    result = service.sync_portfolios(repo, FakeMetaClient(run2), None)
    assert result["portfolios"]["removed"] == 1  # biz_B
    assert result["accounts"]["created"] == 1  # act_4
    assert result["accounts"]["updated"] == 1  # act_1
    assert result["accounts"]["removed"] == 2  # act_2 (plus dans A) + act_3 (B retiré)

    # La vue ne renvoie que l'actif.
    view = service.list_portfolios(repo)
    assert len(view["portfolios"]) == 1
    account_names = {a["name"] for p in view["portfolios"] for a in p["accounts"]}
    assert account_names == {"Acc1 renommé", "Acc4"}


def test_sync_is_idempotent(db_session):
    repo = PortfolioRepository(db_session)
    service.sync_portfolios(repo, FakeMetaClient(_RUN1), None)
    # Re-synchro à l'identique : rien créé ni retiré, tout en "updated".
    result = service.sync_portfolios(repo, FakeMetaClient(_RUN1), None)
    assert result["portfolios"]["created"] == 0
    assert result["accounts"]["created"] == 0
    assert result["portfolios"]["removed"] == 0
    assert result["accounts"]["removed"] == 0
    assert len(service.list_portfolios(repo)["portfolios"]) == 2

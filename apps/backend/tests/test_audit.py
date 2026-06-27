"""Journal d'audit : helpers, accès admin-only, listing."""


def _admin_token(client, db_session) -> str:
    from app.modules.users.seed import seed_admin

    seed_admin(db_session)
    login = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "admin1234"})
    return login.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_audit_helpers():
    from app.modules.audit.recorder import actor_from_auth, humanize, is_auditable

    assert is_auditable("DELETE", "/api/clients/1") is True
    assert is_auditable("GET", "/api/clients") is False  # lectures non journalisées
    assert is_auditable("POST", "/api/audit") is False  # consulter le journal n'est pas une action
    assert is_auditable("POST", "/health") is False
    assert actor_from_auth(None) == {}
    assert actor_from_auth("Bearer pas-un-vrai-token") == {}


def test_audit_humanize_labels():
    from app.modules.audit.recorder import humanize

    # Libellés métier, avec le NOM de l'entité quand il est résolu.
    assert humanize("DELETE", "/api/clients/9", "William Bouzemarene") == "Suppression — client « William Bouzemarene »"
    assert humanize("PATCH", "/api/users/3", "Jean Dupont") == "Modification — utilisateur « Jean Dupont »"
    assert humanize("POST", "/api/clients/5/send-report", "Best Energy") == "Envoi du rapport — client « Best Energy »"
    # Sans nom résolu : type + id, ou libellé d'action seul.
    assert humanize("POST", "/api/clients") == "Création — client"
    assert humanize("DELETE", "/api/clients/1") == "Suppression — client #1"
    assert humanize("POST", "/api/reports/send-day") == "Envoi groupé des rapports"


def test_audit_diff_computes_field_changes():
    from app.modules.audit.recorder import _CLIENT_FIELDS, _diff
    from app.modules.clients.models import Client

    before = {
        "name": "Acme",
        "company": "Acme SA",
        "contact_name": None,
        "phone": None,
        "emails": ["a@x.com"],
        "meta_business_id": None,
        "managed_campaign_ids": [],
        "report_day": 0,
        "is_active": True,
    }
    after = Client(
        name="Acme",
        company="Acme SA",
        emails=["a@x.com"],
        managed_campaign_ids=[],
        report_day=4,
        is_active=False,
    )
    by_field = {c["field"]: c for c in _diff(before, after, _CLIENT_FIELDS)}
    assert "Nom" not in by_field  # inchangé
    assert by_field["Jour d'envoi"] == {"field": "Jour d'envoi", "before": "Lundi", "after": "Vendredi"}
    assert by_field["Actif"] == {"field": "Actif", "before": "Oui", "after": "Non"}


def test_audit_admin_only(client, db_session):
    token = _admin_token(client, db_session)
    assert client.get("/api/audit", headers=_auth(token)).status_code == 200
    assert client.get("/api/audit").status_code == 401  # sans token

    # Un non-admin (expert Meta Ads) ne peut pas consulter le journal.
    client.post(
        "/api/users",
        headers=_auth(token),
        json={
            "firstname": "Ex",
            "lastname": "Pert",
            "email": "expert@x.com",
            "password": "password123",
            "role": "META_ADS_EXPERT",
        },
    )
    expert = client.post("/api/auth/login", json={"email": "expert@x.com", "password": "password123"}).json()
    assert client.get("/api/audit", headers=_auth(expert["access_token"])).status_code == 403


def test_audit_lists_recent_first(client, db_session):
    from app.modules.audit.repository import AuditRepository

    repo = AuditRepository(db_session)
    repo.create(method="POST", path="/api/clients", action="Création clients", status_code=201, actor_email="a@x.com")
    repo.create(
        method="DELETE", path="/api/clients/9", action="Suppression clients", status_code=204, actor_email="a@x.com"
    )

    token = _admin_token(client, db_session)
    body = client.get("/api/audit", headers=_auth(token)).json()
    assert body["total"] >= 2
    assert any(item["path"] == "/api/clients/9" for item in body["items"])
    # Filtre par méthode.
    only_delete = client.get("/api/audit?method=DELETE", headers=_auth(token)).json()
    assert all(item["method"] == "DELETE" for item in only_delete["items"])


def test_audit_filters_actor_and_date(client, db_session):
    from datetime import datetime, timezone

    from app.modules.audit.repository import AuditRepository

    repo = AuditRepository(db_session)
    repo.create(
        method="POST", path="/api/clients", action="Création — client", status_code=201,
        actor_email="alice@x.com", created_at=datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc),
    )
    repo.create(
        method="DELETE", path="/api/clients/9", action="Suppression — client", status_code=204,
        actor_email="bob@x.com", created_at=datetime(2026, 6, 22, 10, 0, tzinfo=timezone.utc),
    )
    token = _admin_token(client, db_session)

    by_actor = client.get("/api/audit?actor=alice", headers=_auth(token)).json()
    assert by_actor["total"] >= 1
    assert all("alice" in (i["actor_email"] or "") for i in by_actor["items"])

    since = client.get("/api/audit?date_from=2026-06-22", headers=_auth(token)).json()
    assert all(i["path"] == "/api/clients/9" for i in since["items"])
    assert all("alice" not in (i["actor_email"] or "") for i in since["items"])

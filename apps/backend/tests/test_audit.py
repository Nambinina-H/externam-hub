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
    assert "Suppression" in humanize("DELETE", "/api/clients/1")
    assert "Création" in humanize("POST", "/api/clients")
    assert "send-report" in humanize("POST", "/api/clients/5/send-report")
    assert actor_from_auth(None) == {}
    assert actor_from_auth("Bearer pas-un-vrai-token") == {}


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

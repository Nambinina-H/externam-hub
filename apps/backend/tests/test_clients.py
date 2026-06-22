from datetime import date


def _admin_token(client, db_session) -> str:
    from app.modules.users.seed import seed_admin

    seed_admin(db_session)
    login = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "admin1234"})
    assert login.status_code == 200
    return login.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_clients_requires_admin(client):
    # Routes clients réservées à l'équipe : sans token -> 401
    assert client.get("/api/clients").status_code == 401


def test_clients_crud(client, db_session):
    token = _admin_token(client, db_session)

    created = client.post(
        "/api/clients",
        headers=_auth(token),
        json={
            "name": "Acme",
            "emails": ["acme@example.com"],
            "report_day": 2,
            "meta_ad_account_id": "act_123",
        },
    )
    assert created.status_code == 201
    body = created.json()
    cid = body["id"]
    assert body["report_day"] == 2
    assert body["is_active"] is True

    listing = client.get("/api/clients", headers=_auth(token))
    assert listing.status_code == 200
    assert listing.json()["total"] == 1

    assert client.get(f"/api/clients/{cid}", headers=_auth(token)).status_code == 200

    updated = client.patch(
        f"/api/clients/{cid}",
        headers=_auth(token),
        json={"report_day": 4, "is_active": False},
    )
    assert updated.status_code == 200
    assert updated.json()["report_day"] == 4
    assert updated.json()["is_active"] is False

    assert client.delete(f"/api/clients/{cid}", headers=_auth(token)).status_code == 204
    assert client.get(f"/api/clients/{cid}", headers=_auth(token)).status_code == 404


def test_managed_campaign_ids_selection(client, db_session):
    token = _admin_token(client, db_session)

    created = client.post(
        "/api/clients",
        headers=_auth(token),
        json={"name": "Acme", "emails": ["acme@example.com"], "report_day": 0},
    )
    cid = created.json()["id"]
    assert created.json()["managed_campaign_ids"] == []  # vide par défaut

    updated = client.patch(
        f"/api/clients/{cid}",
        headers=_auth(token),
        json={"managed_campaign_ids": ["camp_1", "camp_2"]},
    )
    assert updated.status_code == 200
    assert updated.json()["managed_campaign_ids"] == ["camp_1", "camp_2"]

    # Persistance après re-lecture.
    fetched = client.get(f"/api/clients/{cid}", headers=_auth(token))
    assert fetched.json()["managed_campaign_ids"] == ["camp_1", "camp_2"]

    # Retrait d'une campagne.
    removed = client.patch(
        f"/api/clients/{cid}",
        headers=_auth(token),
        json={"managed_campaign_ids": ["camp_2"]},
    )
    assert removed.json()["managed_campaign_ids"] == ["camp_2"]


def test_send_report_now(client, db_session, monkeypatch):
    captured = {}

    def fake_send_email(to, subject, html):
        captured.update(to=to, subject=subject, html=html)

    monkeypatch.setattr("app.modules.reports.service.send_email", fake_send_email)

    token = _admin_token(client, db_session)
    cid = client.post(
        "/api/clients",
        headers=_auth(token),
        json={"name": "Beta", "emails": ["beta@example.com"], "report_day": 0, "meta_ad_account_id": "act_9"},
    ).json()["id"]

    res = client.post(f"/api/clients/{cid}/send-report", headers=_auth(token))
    assert res.status_code == 200
    assert res.json()["recipients"] == ["beta@example.com"]

    assert captured["to"] == ["beta@example.com"]
    assert "Beta" in captured["subject"]
    assert "Merci de votre confiance." in captured["html"]  # note de clôture par défaut présente

    got = client.get(f"/api/clients/{cid}", headers=_auth(token)).json()
    assert got["last_report_sent_at"] is not None


def test_send_report_chosen_recipient(client, db_session, monkeypatch):
    captured = {}
    monkeypatch.setattr("app.modules.reports.service.send_email", lambda to, subject, html: captured.update(to=to))

    token = _admin_token(client, db_session)
    cid = client.post(
        "/api/clients",
        headers=_auth(token),
        json={"name": "Multi", "emails": ["a@x.com", "b@x.com"], "report_day": 0},
    ).json()["id"]

    res = client.post(f"/api/clients/{cid}/send-report", headers=_auth(token), json={"to": ["b@x.com"]})
    assert res.status_code == 200
    assert res.json()["recipients"] == ["b@x.com"]
    assert captured["to"] == ["b@x.com"]


def test_report_preview(client, db_session):
    token = _admin_token(client, db_session)
    cid = client.post(
        "/api/clients",
        headers=_auth(token),
        json={"name": "PreviewCo", "emails": ["p@example.com"], "report_day": 0},
    ).json()["id"]

    res = client.get(f"/api/clients/{cid}/report-preview", headers=_auth(token))
    assert res.status_code == 200
    body = res.json()
    assert "PreviewCo" in body["subject"]  # {{client}} résolu dans l'objet
    assert body["start"] and body["end"]


def test_send_day_reports(client, db_session, monkeypatch):
    sent: list[str] = []
    monkeypatch.setattr("app.modules.reports.service.send_email", lambda to, subject, html: sent.extend(to))

    token = _admin_token(client, db_session)
    weekday = date.today().weekday()
    for name, email in [("D1", "d1@x.com"), ("D2", "d2@x.com")]:
        client.post(
            "/api/clients",
            headers=_auth(token),
            json={"name": name, "emails": [email], "report_day": weekday, "is_active": True},
        )

    res = client.post("/api/reports/send-day", headers=_auth(token))
    assert res.status_code == 200
    assert res.json()["sent"] == 2
    assert set(sent) == {"d1@x.com", "d2@x.com"}


def test_weekly_reports_filtered_by_day(client, db_session, monkeypatch):
    recipients: list[str] = []
    monkeypatch.setattr(
        "app.modules.reports.service.send_email",
        lambda to, subject, html: recipients.extend(to),
    )

    token = _admin_token(client, db_session)
    for name, email, day, active in [
        ("A", "a@example.com", 0, True),
        ("B", "b@example.com", 0, True),
        ("C", "c@example.com", 1, True),
        ("D", "d@example.com", 0, False),
    ]:
        client.post(
            "/api/clients",
            headers=_auth(token),
            json={"name": name, "emails": [email], "report_day": day, "is_active": active},
        )

    from app.modules.reports.service import send_weekly_reports_for_day

    # Lundi (0) : 2 clients actifs (A, B) ; C est mardi, D est inactif.
    result = send_weekly_reports_for_day(db_session, 0, today=date(2026, 6, 15))
    assert result == {"sent": 2, "failed": 0, "total": 2}
    assert set(recipients) == {"a@example.com", "b@example.com"}


_CSV = (
    "NOM,Entreprise,Téléphone,Emails\n"
    "Jean Acme,Acme SA,0612345678,jean@acme.com\n"
    'Marie Globex,Globex Corp,0700000000,"marie@globex.com, ops@globex.com"\n'
    "Jean Acme,Acme SA,0600000000,dup@acme.com\n"  # même nom -> upsert (mise à jour)
    ",X,0600000000,x@y.com\n"  # sans nom -> ignoré
)


def test_import_preview(client, db_session):
    token = _admin_token(client, db_session)
    res = client.post("/api/clients/import/preview", headers=_auth(token), json={"csv": _CSV})
    assert res.status_code == 200
    body = res.json()
    assert body["headers"] == ["NOM", "Entreprise", "Téléphone", "Emails"]
    assert body["count"] == 4
    assert len(body["sample"]) == 4


def test_import_clients_upsert_with_mapping(client, db_session):
    token = _admin_token(client, db_session)
    res = client.post(
        "/api/clients/import",
        headers=_auth(token),
        json={
            "csv": _CSV,
            "mapping": {"name": "NOM", "company": "Entreprise", "phone": "Téléphone", "emails": "Emails"},
        },
    )
    assert res.status_code == 200
    # 2 créés (Jean Acme, Marie Globex), 1 mis à jour (Jean Acme en doublon), 1 ignoré (sans nom).
    assert res.json() == {"created": 2, "updated": 1, "skipped": 1}

    listing = client.get("/api/clients", headers=_auth(token)).json()
    assert listing["total"] == 2
    globex = next(c for c in listing["items"] if c["name"] == "Marie Globex")
    assert globex["emails"] == ["marie@globex.com", "ops@globex.com"]
    assert globex["company"] == "Globex Corp"
    # upsert : la 2e ligne "Jean Acme" a mis à jour ses emails.
    acme = next(c for c in listing["items"] if c["name"] == "Jean Acme")
    assert acme["emails"] == ["dup@acme.com"]
    assert acme["company"] == "Acme SA"


def test_auto_link_clients_by_coherence(db_session):
    from app.modules.clients import service
    from app.modules.clients.models import Client
    from app.modules.clients.repository import ClientRepository

    repo = ClientRepository(db_session)
    repo.create(
        Client(
            name="William Bouzemarene",
            company="Energy Control",
            emails=["william.bouzemarene@best-energy-control.fr"],  # domaine -> portefeuille
            report_day=0,
            is_active=True,
        )
    )
    repo.create(
        Client(
            name="Vladimir Constantin",
            company="Swiss immobilier",  # entreprise -> compte du portefeuille
            emails=[],
            report_day=0,
            is_active=True,
        )
    )
    repo.create(
        Client(name="Inconnu", company="ZZZ Rien", emails=[], report_day=0, is_active=True)
    )

    portfolios = [
        {"id": "biz_energy", "name": "Best Energy Control Pubs", "accounts": [{"name": "BEST ENERGY CONTROL"}]},
        {"id": "biz_immo", "name": "Immobilier", "accounts": [{"name": "Swiss-immobilier"}]},
    ]
    linked = service.auto_link_clients(repo, portfolios)
    assert linked == 2

    by_name = {c.name: c for c in repo.list_all()}
    assert by_name["William Bouzemarene"].meta_business_id == "biz_energy"
    assert by_name["Vladimir Constantin"].meta_business_id == "biz_immo"
    assert by_name["Inconnu"].meta_business_id is None


def test_auto_link_does_not_invent_on_shared_company(db_session):
    """Société + domaine email partagés (Malakoff Humanis) : on lie par le NOM, sinon rien."""
    from app.modules.clients import service
    from app.modules.clients.models import Client
    from app.modules.clients.repository import ClientRepository

    repo = ClientRepository(db_session)
    repo.create(
        Client(
            name="Ludovic Belin",
            company="Malakoff Humanis",
            emails=["ludovic.belin-age@malakoffhumanis.com"],
            report_day=0,
            is_active=True,
        )
    )
    repo.create(
        Client(
            name="Mystere Anonyme",  # aucun portefeuille ne porte ce nom
            company="Malakoff Humanis",
            emails=["mystere@malakoffhumanis.com"],
            report_day=0,
            is_active=True,
        )
    )
    portfolios = [
        {"id": "biz_gaylord", "name": "Gaylord Le Peltier - Malakoff Humanis", "accounts": [{"name": "Gaylord"}]},
        {"id": "biz_belin", "name": "Portefeuille Belin Malakoff Humanis", "accounts": [{"name": "BELIN"}]},
    ]
    linked = service.auto_link_clients(repo, portfolios)
    assert linked == 1

    by_name = {c.name: c for c in repo.list_all()}
    assert by_name["Ludovic Belin"].meta_business_id == "biz_belin"  # via "belin", pas la société partagée
    assert by_name["Mystere Anonyme"].meta_business_id is None  # ambigu -> non lié


def test_send_email_maps_smtp_auth_error_to_domain_error(monkeypatch):
    """Identifiants SMTP refusés (Gmail 535) → EmailDeliveryError (502, message actionnable),
    jamais un 500 brut côté API."""
    import smtplib

    import pytest

    from app.core import email as email_mod
    from app.core.errors import EmailDeliveryError
    from app.modules.settings.service import SmtpConfig

    # SMTP « configuré » sinon send_email part en dry-run et n'atteint jamais le serveur.
    monkeypatch.setattr(
        "app.modules.settings.service.get_effective_smtp",
        lambda: SmtpConfig(host="smtp.test", port=587, user="u@test.com", password="x", from_email="u@test.com"),
    )

    class _FakeSMTP:
        def __init__(self, host, port):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def starttls(self):
            pass

        def login(self, user, password):
            raise smtplib.SMTPAuthenticationError(535, b"5.7.8 BadCredentials")

        def send_message(self, msg):
            pass

    monkeypatch.setattr(smtplib, "SMTP", _FakeSMTP)

    with pytest.raises(EmailDeliveryError) as err:
        email_mod.send_email("client@x.com", "Sujet", "<p>Bonjour</p>")
    assert err.value.status_code == 502
    assert "mot de passe d'application" in err.value.detail

def _admin_token(client, db_session) -> str:
    from app.modules.users.seed import seed_admin

    seed_admin(db_session)
    login = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "admin1234"})
    return login.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _new_client(client, token, name="Gamma", emails=("g@x.com",)) -> int:
    return client.post(
        "/api/clients",
        headers=_auth(token),
        json={"name": name, "emails": list(emails), "report_day": 0},
    ).json()["id"]


def test_base_template_default_and_update(client, db_session):
    token = _admin_token(client, db_session)
    base = client.get("/api/reports/template", headers=_auth(token)).json()
    assert "{{client}}" in base["subject"]  # placeholders du modèle par défaut
    assert base["is_override"] is False

    upd = client.put(
        "/api/reports/template",
        headers=_auth(token),
        json={"subject": "Hebdo {{client}}", "intro": "Salut {{client}} !", "closing": "Merci"},
    )
    assert upd.status_code == 200
    assert upd.json()["subject"] == "Hebdo {{client}}"
    # persistance
    assert client.get("/api/reports/template", headers=_auth(token)).json()["intro"] == "Salut {{client}} !"


def test_client_override_lifecycle(client, db_session):
    token = _admin_token(client, db_session)
    cid = _new_client(client, token)

    # hérite de la base au départ
    assert client.get(f"/api/reports/template/client/{cid}", headers=_auth(token)).json()["is_override"] is False

    over = client.put(
        f"/api/reports/template/client/{cid}",
        headers=_auth(token),
        json={"subject": "Perso {{client}}", "intro": "Bonjour {{entreprise}}", "closing": "Bye"},
    )
    assert over.status_code == 200
    assert over.json()["is_override"] is True
    assert cid in client.get("/api/reports/template/overrides", headers=_auth(token)).json()

    got = client.get(f"/api/reports/template/client/{cid}", headers=_auth(token)).json()
    assert got["subject"] == "Perso {{client}}" and got["is_override"] is True

    # suppression -> retour au modèle de base
    assert client.delete(f"/api/reports/template/client/{cid}", headers=_auth(token)).status_code == 200
    assert client.get(f"/api/reports/template/client/{cid}", headers=_auth(token)).json()["is_override"] is False
    assert cid not in client.get("/api/reports/template/overrides", headers=_auth(token)).json()


def test_template_preview_resolves_placeholders(client, db_session):
    token = _admin_token(client, db_session)
    res = client.post(
        "/api/reports/template/preview",
        headers=_auth(token),
        json={"subject": "Obj {{client}}", "intro": "Dépenses : {{depenses}}", "closing": "Fin"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["subject"] == "Obj Client Exemple"
    assert "CTR" in body["html"]  # tableau par campagne présent
    assert "TOTAL" in body["html"]  # ligne total par campagne
    assert "€" in body["html"]  # {{depenses}} résolu (données d'exemple)


def test_client_override_used_when_sending(client, db_session, monkeypatch):
    captured = {}
    monkeypatch.setattr(
        "app.modules.reports.service.send_email",
        lambda to, subject, html: captured.update(subject=subject, html=html),
    )
    token = _admin_token(client, db_session)
    cid = _new_client(client, token, name="Gamma", emails=["g@x.com"])

    client.put(
        f"/api/reports/template/client/{cid}",
        headers=_auth(token),
        json={"subject": "SPECIAL {{client}}", "intro": "Hello {{client}}", "closing": "."},
    )
    res = client.post(f"/api/clients/{cid}/send-report", headers=_auth(token))
    assert res.status_code == 200
    assert captured["subject"] == "SPECIAL Gamma"
    assert "Hello Gamma" in captured["html"]


def test_report_lists_managed_campaigns(db_session):
    """Le rapport détaille les campagnes GÉRÉES, groupées par compte, avec un total."""
    from app.modules.ads.models import MetaAdAccount, MetaPortfolio
    from app.modules.ads.provider import get_account_campaigns
    from app.modules.clients.models import Client
    from app.modules.clients.repository import ClientRepository
    from app.modules.reports.service import preview_report

    db_session.add(MetaPortfolio(business_id="biz_x", name="Portef X"))
    db_session.add(MetaAdAccount(id="act_77", account_id="77", name="Compte A", business_id="biz_x"))
    db_session.commit()

    chosen = get_account_campaigns("act_77")[0]  # campagne (stub) du compte
    client_obj = ClientRepository(db_session).create(
        Client(
            name="ClientX",
            emails=["x@x.com"],
            report_day=0,
            meta_business_id="biz_x",
            managed_campaign_ids=[chosen["id"]],
        )
    )

    html = preview_report(db_session, client_obj)["html"]
    assert "TOTAL" in html  # ligne total de la campagne
    # Seule la campagne COCHÉE est rendue (1 seule ligne TOTAL), pas toutes celles du compte.
    assert html.count("TOTAL") == 1
    assert "Aucune campagne" not in html

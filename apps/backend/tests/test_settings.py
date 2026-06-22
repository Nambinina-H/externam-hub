def _admin_token(client, db_session) -> str:
    from app.modules.users.seed import seed_admin

    seed_admin(db_session)
    login = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "admin1234"})
    return login.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_email_settings_requires_admin(client):
    assert client.get("/api/settings/email").status_code == 401


def test_email_settings_default_source_env(client, db_session):
    token = _admin_token(client, db_session)
    res = client.get("/api/settings/email", headers=_auth(token))
    assert res.status_code == 200
    body = res.json()
    # En test, le .env n'a pas de SMTP_USER -> source env, mot de passe non défini.
    assert body["source"] == "env"
    assert body["password_set"] is False


def test_update_email_settings_hides_password(client, db_session):
    token = _admin_token(client, db_session)
    res = client.put(
        "/api/settings/email",
        headers=_auth(token),
        json={
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_user": "sender@gmail.com",
            "from_email": "sender@gmail.com",
            "smtp_password": "app-password-123",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["source"] == "db"
    assert body["smtp_user"] == "sender@gmail.com"
    assert body["password_set"] is True
    # Le mot de passe ne doit JAMAIS être renvoyé.
    assert "smtp_password" not in body and "password" not in body

    # Mise à jour sans mot de passe -> on conserve l'ancien.
    res2 = client.put(
        "/api/settings/email",
        headers=_auth(token),
        json={"smtp_host": "smtp.gmail.com", "smtp_port": 465, "smtp_user": "sender@gmail.com",
              "from_email": "sender@gmail.com"},
    )
    assert res2.json()["password_set"] is True
    assert res2.json()["smtp_port"] == 465


def test_smtp_password_encrypted_and_resolved(db_session):
    """Le mot de passe est chiffré en base mais déchiffrable via la config effective."""
    from app.modules.settings import service
    from app.modules.settings.repository import EmailSettingsRepository
    from app.modules.settings.schemas import EmailSettingsUpdate

    repo = EmailSettingsRepository(db_session)
    service.update_settings(
        repo,
        EmailSettingsUpdate(
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_user="sender@gmail.com",
            from_email="sender@gmail.com",
            smtp_password="secret-app-pw",
        ),
    )
    row = repo.get()
    assert row.smtp_password_enc and row.smtp_password_enc != "secret-app-pw"  # stocké chiffré

    cfg = service.resolve_smtp(db_session)
    assert cfg.user == "sender@gmail.com"
    assert cfg.password == "secret-app-pw"  # déchiffré pour l'envoi


def test_test_email_endpoint(client, db_session, monkeypatch):
    captured = {}
    monkeypatch.setattr("app.modules.settings.service.send_email", lambda to, subject, html: captured.update(to=to))

    token = _admin_token(client, db_session)
    res = client.post("/api/settings/email/test", headers=_auth(token), json={"to": "tester@example.com"})
    assert res.status_code == 200
    assert res.json()["to"] == "tester@example.com"
    assert captured["to"] == "tester@example.com"

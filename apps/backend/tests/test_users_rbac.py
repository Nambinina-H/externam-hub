def _superadmin_token(client, db_session) -> str:
    from app.modules.users.seed import seed_admin

    seed_admin(db_session)  # seedé en SUPERADMIN
    login = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "admin1234"})
    return login.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_superadmin_creates_meta_ads_expert(client, db_session):
    token = _superadmin_token(client, db_session)
    res = client.post(
        "/api/users",
        headers=_auth(token),
        json={
            "firstname": "Eva",
            "lastname": "Expert",
            "email": "eva@example.com",
            "password": "expert1234",
            "role": "META_ADS_EXPERT",
        },
    )
    assert res.status_code == 201
    assert res.json()["role"] == "META_ADS_EXPERT"

    # Doublon d'email -> 400
    dup = client.post(
        "/api/users",
        headers=_auth(token),
        json={"firstname": "X", "lastname": "Y", "email": "eva@example.com", "password": "expert1234",
              "role": "META_ADS_EXPERT"},
    )
    assert dup.status_code == 400


def test_meta_ads_expert_access_scope(client, db_session):
    admin = _superadmin_token(client, db_session)
    client.post(
        "/api/users",
        headers=_auth(admin),
        json={"firstname": "Eva", "lastname": "Expert", "email": "eva@example.com",
              "password": "expert1234", "role": "META_ADS_EXPERT"},
    )
    expert = client.post("/api/auth/login", json={"email": "eva@example.com", "password": "expert1234"}).json()[
        "access_token"
    ]

    # L'expert accède à l'espace Meta Ads...
    assert client.get("/api/clients", headers=_auth(expert)).status_code == 200
    assert client.get("/api/settings/email", headers=_auth(expert)).status_code == 200
    # ... mais pas à l'administration (gestion des utilisateurs).
    assert client.get("/api/users", headers=_auth(expert)).status_code == 403
    assert client.post(
        "/api/users",
        headers=_auth(expert),
        json={"firstname": "Z", "lastname": "Z", "email": "z@example.com", "password": "zzzzzzzz",
              "role": "META_ADS_EXPERT"},
    ).status_code == 403


def _create_expert(client, admin_token) -> int:
    return client.post(
        "/api/users",
        headers=_auth(admin_token),
        json={"firstname": "Eva", "lastname": "Expert", "email": "eva@example.com",
              "password": "expert1234", "role": "META_ADS_EXPERT"},
    ).json()["id"]


def test_superadmin_updates_user(client, db_session):
    token = _superadmin_token(client, db_session)
    uid = _create_expert(client, token)

    res = client.patch(
        f"/api/users/{uid}",
        headers=_auth(token),
        json={"lastname": "Nouveau", "role": "SUPERADMIN"},
    )
    assert res.status_code == 200
    assert res.json()["lastname"] == "Nouveau"
    assert res.json()["role"] == "SUPERADMIN"

    # Le nouveau mot de passe permet de se connecter.
    client.patch(f"/api/users/{uid}", headers=_auth(token), json={"password": "newpass123"})
    login = client.post("/api/auth/login", json={"email": "eva@example.com", "password": "newpass123"})
    assert login.status_code == 200


def test_superadmin_deletes_user(client, db_session):
    token = _superadmin_token(client, db_session)
    uid = _create_expert(client, token)

    assert client.delete(f"/api/users/{uid}", headers=_auth(token)).status_code == 204
    # Plus connectable.
    assert client.post("/api/auth/login", json={"email": "eva@example.com", "password": "expert1234"}).status_code != 200


def test_superadmin_cannot_delete_or_demote_self(client, db_session):
    token = _superadmin_token(client, db_session)
    me = client.get("/api/users/me", headers=_auth(token)).json()

    assert client.delete(f"/api/users/{me['id']}", headers=_auth(token)).status_code == 400
    demote = client.patch(f"/api/users/{me['id']}", headers=_auth(token), json={"role": "META_ADS_EXPERT"})
    assert demote.status_code == 400

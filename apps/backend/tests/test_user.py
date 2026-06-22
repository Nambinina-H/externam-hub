def _register(client, email="jane@example.com", password="supersecret"):
    return client.post(
        "/api/auth/register",
        json={"firstname": "Jane", "lastname": "Doe", "email": email, "password": password},
    )


def test_register_returns_tokens(client):
    res = _register(client)
    assert res.status_code == 201
    body = res.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"


def test_register_duplicate_conflict(client):
    assert _register(client, email="dup@example.com").status_code == 201
    res = _register(client, email="dup@example.com")
    assert res.status_code == 409


def test_login_and_me(client):
    _register(client, email="john@example.com", password="supersecret")

    login = client.post("/api/auth/login", json={"email": "john@example.com", "password": "supersecret"})
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "john@example.com"


def test_login_wrong_password(client):
    _register(client, email="k@example.com", password="supersecret")
    res = client.post("/api/auth/login", json={"email": "k@example.com", "password": "wrongpass"})
    assert res.status_code == 401


def test_me_requires_auth(client):
    assert client.get("/api/users/me").status_code == 401


def test_list_users_requires_auth(client):
    # endpoint réservé admin (garde via dependencies=[...]) : sans token -> 401
    assert client.get("/api/users").status_code == 401


def test_admin_seed_can_list_users(client, db_session):
    # seed de l'admin (creds depuis SEED_ADMIN_* du conftest) -> login -> accès à la liste admin
    from app.modules.users.seed import seed_admin

    admin = seed_admin(db_session)
    assert admin is not None
    # idempotent : un 2e appel ne recrée pas
    assert seed_admin(db_session) is None

    login = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "admin1234"})
    assert login.status_code == 200
    token = login.json()["access_token"]

    res = client.get("/api/users", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    body = res.json()
    assert body["total"] >= 1
    assert any(u["email"] == "admin@example.com" for u in body["items"])

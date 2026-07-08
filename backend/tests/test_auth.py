"""Auth (kayit, giris, /me) endpoint testleri."""


def test_register_creates_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "yeni_kullanici@example.com",
            "password": "GucluSifre123",
            "full_name": "Yeni Kullanici",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "yeni_kullanici@example.com"
    assert data["full_name"] == "Yeni Kullanici"
    # Sifre hash'i asla API yanitinda donmemeli
    assert "password" not in data
    assert "password_hash" not in data


def test_register_duplicate_email_fails(client):
    payload = {
        "email": "tekrar@example.com",
        "password": "GucluSifre123",
        "full_name": "Birinci Kayit",
    }
    first = client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201

    second = client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 400


def test_login_success(registered_user, client):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password_fails(registered_user, client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": registered_user["email"], "password": "YanlisSifre"},
    )
    assert response.status_code == 401


def test_get_me_requires_token(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code in (401, 403)


def test_get_me_returns_current_user(registered_user, client):
    response = client.get("/api/v1/auth/me", headers=registered_user["headers"])
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == registered_user["email"]

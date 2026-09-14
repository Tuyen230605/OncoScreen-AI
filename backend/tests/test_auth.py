def test_register_login_me(client):
    r = client.post(
        "/api/v1/auth/register",
        json={"email": "a@b.vn", "password": "123456", "full_name": "A", "role": "patient"},
    )
    assert r.status_code == 201
    r = client.post("/api/v1/auth/login", json={"email": "a@b.vn", "password": "123456"})
    assert r.status_code == 200
    tok = r.json()["access_token"]
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tok}"})
    assert me.json()["email"] == "a@b.vn"


def test_wrong_password(client):
    client.post(
        "/api/v1/auth/register", json={"email": "a@b.vn", "password": "123456", "full_name": "A", "role": "patient"}
    )
    assert client.post("/api/v1/auth/login", json={"email": "a@b.vn", "password": "xxxxxx"}).status_code == 401


def test_health(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200 and r.json()["agent"] == "mock"

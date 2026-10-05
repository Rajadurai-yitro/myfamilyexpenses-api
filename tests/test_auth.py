def test_health_check(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


def test_register_and_login(client):
    # Seed categories first
    client.post("/api/v1/categories/seed")

    # 1. Register
    reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "testuser@example.com",
            "password": "Password123!",
            "display_name": "Test User",
        },
    )
    assert reg_res.status_code == 201
    data = reg_res.json()
    assert data["user"]["email"] == "testuser@example.com"
    assert data["user"]["display_name"] == "Test User"
    assert "access_token" in data
    assert "refresh_token" in data
    access_token = data["access_token"]
    refresh_token = data["refresh_token"]

    # 2. Duplicate registration should fail
    dup_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "testuser@example.com",
            "password": "Password123!",
        },
    )
    assert dup_res.status_code == 409
    assert dup_res.json()["code"] == "RESOURCE_CONFLICT"

    # 3. Login with correct password
    login_res = client.post(
        "/api/v1/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "Password123!",
        },
    )
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()

    # 4. Login with incorrect password
    bad_login = client.post(
        "/api/v1/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "WrongPassword",
        },
    )
    assert bad_login.status_code == 401
    assert bad_login.json()["code"] == "UNAUTHORIZED"

    # 5. Refresh token
    refresh_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_res.status_code == 200
    assert "access_token" in refresh_res.json()

    # 6. Current user /me
    me_res = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_res.status_code == 200
    assert me_res.json()["user"]["email"] == "testuser@example.com"
    assert me_res.json()["settings"]["currency_code"] == "INR"

    # 7. Forgot password
    forgot_res = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "testuser@example.com"},
    )
    assert forgot_res.status_code == 200
    assert "password reset link has been sent" in forgot_res.json()["message"]

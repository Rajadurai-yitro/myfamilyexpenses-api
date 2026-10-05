import base64


_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def _register(client, email="profile_test@example.com"):
    res = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "display_name": "Profile User"},
    )
    assert res.status_code == 201
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_profile_settings_avatar_and_delete(client):
    headers = _register(client)

    renamed = client.patch(
        "/api/v1/users/me",
        headers=headers,
        json={"display_name": "New Name"},
    )
    assert renamed.status_code == 200
    assert renamed.json()["display_name"] == "New Name"
    assert renamed.json()["has_avatar"] is False

    settings = client.patch(
        "/api/v1/users/me/settings",
        headers=headers,
        json={"currency_code": "USD", "time_zone": "America/New_York", "language_code": "ta"},
    )
    assert settings.status_code == 200
    body = settings.json()
    assert body["currency_code"] == "USD"
    assert body["time_zone"] == "America/New_York"
    assert body["language_code"] == "ta"

    uploaded = client.post(
        "/api/v1/users/me/avatar",
        headers=headers,
        files={"file": ("photo.png", _PNG, "image/png")},
    )
    assert uploaded.status_code == 200
    assert uploaded.json()["has_avatar"] is True

    photo = client.get("/api/v1/users/me/avatar", headers=headers)
    assert photo.status_code == 200
    assert photo.content.startswith(b"\x89PNG")

    me = client.get("/api/v1/users/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["user"]["has_avatar"] is True
    assert me.json()["settings"]["time_zone"] == "America/New_York"

    removed = client.delete("/api/v1/users/me/avatar", headers=headers)
    assert removed.status_code == 200
    assert removed.json()["has_avatar"] is False

    deleted = client.delete("/api/v1/users/me", headers=headers)
    assert deleted.status_code == 200

    gone = client.get("/api/v1/users/me", headers=headers)
    assert gone.status_code == 401

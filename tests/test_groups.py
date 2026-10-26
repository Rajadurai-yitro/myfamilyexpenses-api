from datetime import date


def _register(client, email, name=None):
    res = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "display_name": name or email.split("@")[0]},
    )
    assert res.status_code == 201
    return res.json()


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_create_group_and_invite_flow(client):
    admin = _register(client, "group-admin@example.com", "Admin")
    member = _register(client, "group-member@example.com", "Member")
    admin_h = _headers(admin["access_token"])
    member_h = _headers(member["access_token"])

    created = client.post(
        "/api/v1/groups",
        headers=admin_h,
        json={
            "name": "Apartment Roommate",
            "group_type": "roommates",
            "visibility": "private",
            "member_emails": ["group-member@example.com"],
        },
    )
    assert created.status_code == 201
    group = created.json()
    assert group["name"] == "Apartment Roommate"
    assert group["member_count"] == 1
    assert any(item["role"] == "admin" for item in group["members"])

    duplicate = client.post(
        f"/api/v1/groups/{group['id']}/invitations",
        headers=admin_h,
        json={"email": "group-member@example.com"},
    )
    assert duplicate.status_code == 409

    dash = client.get("/api/v1/groups/dashboard", headers=member_h).json()
    invite = next(item for item in dash["updates"] if item["kind"] == "invitation")
    accepted = client.post(
        f"/api/v1/groups/invitations/{invite['invitation_id']}/accept",
        headers=member_h,
    )
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "accepted"

    listed = client.get("/api/v1/groups", headers=member_h).json()
    assert len(listed) == 1
    assert listed[0]["member_count"] == 2

    already = client.post(
        f"/api/v1/groups/{group['id']}/invitations",
        headers=admin_h,
        json={"email": "group-member@example.com"},
    )
    assert already.status_code == 409


def test_reject_invitation(client):
    admin = _register(client, "reject-admin@example.com")
    other = _register(client, "reject-member@example.com")
    created = client.post(
        "/api/v1/groups",
        headers=_headers(admin["access_token"]),
        json={"name": "Trip", "member_emails": ["reject-member@example.com"]},
    ).json()
    dash = client.get("/api/v1/groups/dashboard", headers=_headers(other["access_token"])).json()
    invite = dash["updates"][0]
    rejected = client.post(
        f"/api/v1/groups/invitations/{invite['invitation_id']}/reject",
        headers=_headers(other["access_token"]),
    )
    assert rejected.json()["status"] == "rejected"
    listed = client.get("/api/v1/groups", headers=_headers(other["access_token"])).json()
    assert listed == []
    assert created["name"] == "Trip"


def test_invalid_group_name(client):
    admin = _register(client, "name-admin@example.com")
    res = client.post(
        "/api/v1/groups",
        headers=_headers(admin["access_token"]),
        json={"name": "A"},
    )
    assert res.status_code in (422, 400)

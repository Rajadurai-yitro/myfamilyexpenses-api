from datetime import date


def _register(client, email):
    return client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "display_name": email.split("@")[0]},
    ).json()


def test_private_group_isolation_and_removed_member(client):
    client.post("/api/v1/categories/seed")
    admin = _register(client, "authz-admin@example.com")
    member = _register(client, "authz-member@example.com")
    outsider = _register(client, "authz-out@example.com")
    admin_h = {"Authorization": f"Bearer {admin['access_token']}"}
    member_h = {"Authorization": f"Bearer {member['access_token']}"}
    out_h = {"Authorization": f"Bearer {outsider['access_token']}"}

    group = client.post(
        "/api/v1/groups",
        headers=admin_h,
        json={
            "name": "Secret House",
            "visibility": "private",
            "member_emails": ["authz-member@example.com"],
        },
    ).json()
    dash = client.get("/api/v1/groups/dashboard", headers=member_h).json()
    client.post(
        f"/api/v1/groups/invitations/{dash['updates'][0]['invitation_id']}/accept",
        headers=member_h,
    )

    forbidden = client.get(f"/api/v1/groups/{group['id']}", headers=out_h)
    assert forbidden.status_code == 403

    discover = client.get("/api/v1/groups/discoverable", headers=out_h).json()
    assert all(item["id"] != group["id"] for item in discover)

    food = next(item for item in client.get("/api/v1/categories").json() if item["name_key"] == "food")
    expense = client.post(
        f"/api/v1/groups/{group['id']}/expenses",
        headers=admin_h,
        json={
            "category_id": food["id"],
            "amount": "10.00",
            "expense_date": str(date.today()),
            "paid_by": admin["user"]["id"],
            "participant_ids": [admin["user"]["id"], member["user"]["id"]],
            "split_method": "equal",
        },
    ).json()

    outsider_expense = client.get(
        f"/api/v1/groups/{group['id']}/expenses/{expense['id']}",
        headers=out_h,
    )
    assert outsider_expense.status_code == 403
    outsider_receipt = client.get(
        f"/api/v1/groups/{group['id']}/expenses/{expense['id']}/receipt",
        headers=out_h,
    )
    assert outsider_receipt.status_code in (403, 404)

    client.delete(f"/api/v1/groups/{group['id']}/members/{member['user']['id']}", headers=admin_h)
    revoked = client.get(f"/api/v1/groups/{group['id']}", headers=member_h)
    assert revoked.status_code == 403
    revoked_expense = client.get(
        f"/api/v1/groups/{group['id']}/expenses/{expense['id']}",
        headers=member_h,
    )
    assert revoked_expense.status_code == 403


def test_discoverable_hides_private_details(client):
    admin = _register(client, "disc-admin@example.com")
    outsider = _register(client, "disc-out@example.com")
    admin_h = {"Authorization": f"Bearer {admin['access_token']}"}
    out_h = {"Authorization": f"Bearer {outsider['access_token']}"}
    group = client.post(
        "/api/v1/groups",
        headers=admin_h,
        json={"name": "Open Club", "visibility": "discoverable"},
    ).json()
    listed = client.get("/api/v1/groups/discoverable", headers=out_h).json()
    match = next(item for item in listed if item["id"] == group["id"])
    assert match["name"] == "Open Club"
    assert "members" not in match
    assert "total_expenses" not in match
    details = client.get(f"/api/v1/groups/{group['id']}", headers=out_h)
    assert details.status_code == 403

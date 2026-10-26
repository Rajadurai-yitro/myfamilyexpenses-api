from datetime import date


def _ready(client):
    client.post("/api/v1/categories/seed")
    a = client.post(
        "/api/v1/auth/register",
        json={"email": "settle-a@example.com", "password": "Password123!", "display_name": "A"},
    ).json()
    b = client.post(
        "/api/v1/auth/register",
        json={"email": "settle-b@example.com", "password": "Password123!", "display_name": "B"},
    ).json()
    c = client.post(
        "/api/v1/auth/register",
        json={"email": "settle-c@example.com", "password": "Password123!", "display_name": "C"},
    ).json()
    d = client.post(
        "/api/v1/auth/register",
        json={"email": "settle-d@example.com", "password": "Password123!", "display_name": "D"},
    ).json()
    headers = {"Authorization": f"Bearer {a['access_token']}"}
    group = client.post(
        "/api/v1/groups",
        headers=headers,
        json={
            "name": "Room",
            "member_emails": [b["user"]["email"], c["user"]["email"], d["user"]["email"]],
        },
    ).json()
    for user in (b, c, d):
        dash = client.get(
            "/api/v1/groups/dashboard",
            headers={"Authorization": f"Bearer {user['access_token']}"},
        ).json()
        invite = next(item for item in dash["updates"] if item["kind"] == "invitation")
        client.post(
            f"/api/v1/groups/invitations/{invite['invitation_id']}/accept",
            headers={"Authorization": f"Bearer {user['access_token']}"},
        )
    food = next(item for item in client.get("/api/v1/categories").json() if item["name_key"] == "food")
    ids = [a["user"]["id"], b["user"]["id"], c["user"]["id"], d["user"]["id"]]
    client.post(
        f"/api/v1/groups/{group['id']}/expenses",
        headers=headers,
        json={
            "category_id": food["id"],
            "amount": "1200.00",
            "expense_date": str(date.today()),
            "paid_by": ids[0],
            "participant_ids": ids,
            "split_method": "equal",
        },
    )
    return group["id"], headers, ids, b


def test_partial_settlement_does_not_clear_full_debt(client):
    group_id, headers, ids, b = _ready(client)
    recorded = client.post(
        f"/api/v1/groups/{group_id}/settlements",
        headers={"Authorization": f"Bearer {b['access_token']}"},
        json={
            "from_user_id": ids[1],
            "to_user_id": ids[0],
            "amount": "200.00",
            "method": "upi",
            "client_request_id": "set-1",
        },
    )
    assert recorded.status_code == 201
    assert recorded.json()["recording_kind"] == "manual"
    balances = {
        item["user_id"]: item["net_amount"]
        for item in client.get(f"/api/v1/groups/{group_id}/balances", headers=headers).json()
    }
    assert balances[ids[0]] == "700.00"
    assert balances[ids[1]] == "-100.00"
    assert balances[ids[2]] == "-300.00"

    overpay = client.post(
        f"/api/v1/groups/{group_id}/settlements",
        headers={"Authorization": f"Bearer {b['access_token']}"},
        json={
            "from_user_id": ids[1],
            "to_user_id": ids[0],
            "amount": "500.00",
            "method": "cash",
        },
    )
    assert overpay.status_code == 422

    duplicate = client.post(
        f"/api/v1/groups/{group_id}/settlements",
        headers={"Authorization": f"Bearer {b['access_token']}"},
        json={
            "from_user_id": ids[1],
            "to_user_id": ids[0],
            "amount": "200.00",
            "method": "upi",
            "client_request_id": "set-1",
        },
    )
    assert duplicate.status_code == 201
    assert duplicate.json()["id"] == recorded.json()["id"]

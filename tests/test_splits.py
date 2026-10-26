from datetime import date


def _setup_group(client):
    client.post("/api/v1/categories/seed")
    users = []
    for email in [
        "split-a@example.com",
        "split-b@example.com",
        "split-c@example.com",
        "split-d@example.com",
    ]:
        res = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "Password123!", "display_name": email[6]},
        ).json()
        users.append(res)
    admin_h = {"Authorization": f"Bearer {users[0]['access_token']}"}
    created = client.post(
        "/api/v1/groups",
        headers=admin_h,
        json={
            "name": "Dinner Club",
            "member_emails": [item["user"]["email"] for item in users[1:]],
        },
    ).json()
    for user in users[1:]:
        dash = client.get(
            "/api/v1/groups/dashboard",
            headers={"Authorization": f"Bearer {user['access_token']}"},
        ).json()
        invite = next(item for item in dash["updates"] if item["kind"] == "invitation")
        client.post(
            f"/api/v1/groups/invitations/{invite['invitation_id']}/accept",
            headers={"Authorization": f"Bearer {user['access_token']}"},
        )
    food = next(c for c in client.get("/api/v1/categories").json() if c["name_key"] == "food")
    ids = [item["user"]["id"] for item in users]
    return created["id"], admin_h, food["id"], ids, users


def test_equal_split_and_payer_excluded(client):
    group_id, headers, food_id, ids, _users = _setup_group(client)
    included = client.post(
        f"/api/v1/groups/{group_id}/expenses",
        headers=headers,
        json={
            "category_id": food_id,
            "amount": "1200.00",
            "expense_date": str(date.today()),
            "paid_by": ids[0],
            "participant_ids": ids,
            "split_method": "equal",
            "client_request_id": "eq-1",
        },
    )
    assert included.status_code == 201
    shares = {item["user_id"]: item["amount"] for item in included.json()["shares"]}
    assert set(shares.values()) == {"300.00"}
    balances = {
        item["user_id"]: item["net_amount"]
        for item in client.get(f"/api/v1/groups/{group_id}/balances", headers=headers).json()
    }
    assert balances[ids[0]] == "900.00"
    assert balances[ids[1]] == "-300.00"

    excluded = client.post(
        f"/api/v1/groups/{group_id}/expenses",
        headers=headers,
        json={
            "category_id": food_id,
            "amount": "90.00",
            "expense_date": str(date.today()),
            "paid_by": ids[0],
            "participant_ids": ids[1:],
            "split_method": "equal",
            "client_request_id": "eq-2",
        },
    )
    assert excluded.status_code == 201
    assert ids[0] not in {item["user_id"] for item in excluded.json()["shares"]}
    assert sum(float(item["amount"]) for item in excluded.json()["shares"]) == 90.0


def test_percent_and_exact_validation(client):
    group_id, headers, food_id, ids, _users = _setup_group(client)
    bad_percent = client.post(
        f"/api/v1/groups/{group_id}/expenses",
        headers=headers,
        json={
            "category_id": food_id,
            "amount": "100.00",
            "expense_date": str(date.today()),
            "paid_by": ids[0],
            "participant_ids": ids[:2],
            "split_method": "percent",
            "shares": [
                {"user_id": ids[0], "percent": "40"},
                {"user_id": ids[1], "percent": "40"},
            ],
        },
    )
    assert bad_percent.status_code == 422

    good_percent = client.post(
        f"/api/v1/groups/{group_id}/expenses",
        headers=headers,
        json={
            "category_id": food_id,
            "amount": "100.00",
            "expense_date": str(date.today()),
            "paid_by": ids[0],
            "participant_ids": ids[:2],
            "split_method": "percent",
            "shares": [
                {"user_id": ids[0], "percent": "40"},
                {"user_id": ids[1], "percent": "60"},
            ],
            "client_request_id": "pct-1",
        },
    )
    assert good_percent.status_code == 201

    bad_exact = client.post(
        f"/api/v1/groups/{group_id}/expenses",
        headers=headers,
        json={
            "category_id": food_id,
            "amount": "100.00",
            "expense_date": str(date.today()),
            "paid_by": ids[0],
            "participant_ids": ids[:2],
            "split_method": "exact",
            "shares": [
                {"user_id": ids[0], "amount": "10.00"},
                {"user_id": ids[1], "amount": "20.00"},
            ],
        },
    )
    assert bad_exact.status_code == 422

    shares = client.post(
        f"/api/v1/groups/{group_id}/expenses",
        headers=headers,
        json={
            "category_id": food_id,
            "amount": "100.00",
            "expense_date": str(date.today()),
            "paid_by": ids[0],
            "participant_ids": ids[:2],
            "split_method": "shares",
            "shares": [
                {"user_id": ids[0], "shares": 1},
                {"user_id": ids[1], "shares": 3},
            ],
            "client_request_id": "sh-1",
        },
    )
    assert shares.status_code == 201
    amounts = {item["user_id"]: item["amount"] for item in shares.json()["shares"]}
    assert amounts[ids[0]] == "25.00"
    assert amounts[ids[1]] == "75.00"


def test_duplicate_expense_request(client):
    group_id, headers, food_id, ids, _users = _setup_group(client)
    body = {
        "category_id": food_id,
        "amount": "50.00",
        "expense_date": str(date.today()),
        "paid_by": ids[0],
        "participant_ids": ids[:2],
        "split_method": "equal",
        "client_request_id": "dup-exp",
    }
    first = client.post(f"/api/v1/groups/{group_id}/expenses", headers=headers, json=body)
    second = client.post(f"/api/v1/groups/{group_id}/expenses", headers=headers, json=body)
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]

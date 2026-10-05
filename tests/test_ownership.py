from datetime import date


def test_user_ownership_enforcement(client):
    # Seed categories
    seed_res = client.post("/api/v1/categories/seed")
    categories = seed_res.json()
    cat_id = categories[0]["id"]

    # Register User A
    user_a = client.post(
        "/api/v1/auth/register",
        json={"email": "usera@example.com", "password": "Password123!"},
    ).json()
    token_a = user_a["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Register User B
    user_b = client.post(
        "/api/v1/auth/register",
        json={"email": "userb@example.com", "password": "Password123!"},
    ).json()
    token_b = user_b["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A creates an expense
    created = client.post(
        "/api/v1/expenses",
        headers=headers_a,
        json={
            "category_id": cat_id,
            "amount": 99.99,
            "expense_date": str(date.today()),
            "description": "User A Private Expense",
        },
    ).json()
    expense_id = created["id"]

    # User B tries to GET User A's expense -> Must be 403 Forbidden!
    forbidden_get = client.get(f"/api/v1/expenses/{expense_id}", headers=headers_b)
    assert forbidden_get.status_code == 403
    assert forbidden_get.json()["code"] == "FORBIDDEN"

    # User B tries to PATCH User A's expense -> Must be 403 Forbidden!
    forbidden_patch = client.patch(
        f"/api/v1/expenses/{expense_id}",
        headers=headers_b,
        json={"amount": 10.00},
    )
    assert forbidden_patch.status_code == 403
    assert forbidden_patch.json()["code"] == "FORBIDDEN"

    # User B tries to DELETE User A's expense -> Must be 403 Forbidden!
    forbidden_del = client.delete(f"/api/v1/expenses/{expense_id}", headers=headers_b)
    assert forbidden_del.status_code == 403
    assert forbidden_del.json()["code"] == "FORBIDDEN"

    # User B lists expenses -> Should NOT see User A's expense!
    list_b = client.get("/api/v1/expenses", headers=headers_b).json()
    assert list_b["total"] == 0
    assert len(list_b["items"]) == 0

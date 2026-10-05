from datetime import date


def test_expense_crud(client):
    # Seed categories
    seed_res = client.post("/api/v1/categories/seed")
    categories = seed_res.json()
    food_cat = next(c for c in categories if c["name_key"] == "food")

    # Register user
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": "expense_test@example.com", "password": "Password123!"},
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Expense
    create_res = client.post(
        "/api/v1/expenses",
        headers=headers,
        json={
            "category_id": food_cat["id"],
            "amount": 250.50,
            "expense_date": str(date.today()),
            "description": "Lunch with family",
        },
    )
    assert create_res.status_code == 201
    expense_data = create_res.json()
    expense_id = expense_data["id"]
    assert expense_data["amount"] == 250.50
    assert expense_data["description"] == "Lunch with family"

    # 2. Get Expense by ID
    get_res = client.get(f"/api/v1/expenses/{expense_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == expense_id

    # 3. List Expenses
    list_res = client.get("/api/v1/expenses", headers=headers)
    assert list_res.status_code == 200
    assert list_res.json()["total"] == 1
    assert len(list_res.json()["items"]) == 1

    # 4. Update Expense
    patch_res = client.patch(
        f"/api/v1/expenses/{expense_id}",
        headers=headers,
        json={"amount": 300.00, "description": "Updated Lunch"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["amount"] == 300.00
    assert patch_res.json()["description"] == "Updated Lunch"

    # 5. Delete Expense
    del_res = client.delete(f"/api/v1/expenses/{expense_id}", headers=headers)
    assert del_res.status_code == 200

    # 6. Verify deleted
    get_again = client.get(f"/api/v1/expenses/{expense_id}", headers=headers)
    assert get_again.status_code == 404


def test_credit_income_and_bill(client):
    categories = client.post("/api/v1/categories/seed").json()
    salary = next(c for c in categories if c["name_key"] == "salary")
    food = next(c for c in categories if c["name_key"] == "food")
    assert salary["kind"] == "credit"
    assert food["kind"] == "debit"

    reg = client.post(
        "/api/v1/auth/register",
        json={"email": "credit_test@example.com", "password": "Password123!"},
    )
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}
    today = str(date.today())

    mismatch = client.post(
        "/api/v1/expenses",
        headers=headers,
        json={
            "category_id": food["id"],
            "amount": 100,
            "expense_date": today,
            "entry_type": "credit",
        },
    )
    assert mismatch.status_code == 422

    created = client.post(
        "/api/v1/expenses",
        headers=headers,
        json={
            "category_id": salary["id"],
            "amount": 1000,
            "expense_date": today,
            "entry_type": "credit",
            "description": "Monthly salary",
        },
    )
    assert created.status_code == 201
    expense_id = created.json()["id"]
    assert created.json()["entry_type"] == "credit"
    assert created.json()["receipt_url"] is None

    png = bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
        "890000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
    )
    upload = client.post(
        f"/api/v1/expenses/{expense_id}/receipt",
        headers=headers,
        files={"file": ("bill.png", png, "image/png")},
    )
    assert upload.status_code == 200
    assert upload.json()["receipt_url"].endswith("/receipt")

    bill = client.get(f"/api/v1/expenses/{expense_id}/receipt", headers=headers)
    assert bill.status_code == 200
    assert bill.content.startswith(b"\x89PNG")

    summary = client.get("/api/v1/reports/summary", headers=headers)
    assert summary.status_code == 200
    assert summary.json()["total_income"] == 1000
    assert summary.json()["total_expense"] == 0


def test_payment_mode_and_new_categories(client):
    categories = client.post("/api/v1/categories/seed").json()
    keys = {item["name_key"] for item in categories}
    assert {"maintenance", "vegetables", "fruits", "entertainment"} <= keys
    food = next(item for item in categories if item["name_key"] == "food")

    reg = client.post(
        "/api/v1/auth/register",
        json={"email": "payment_test@example.com", "password": "Password123!"},
    )
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}
    today = str(date.today())

    missing_txn = client.post(
        "/api/v1/expenses",
        headers=headers,
        json={
            "category_id": food["id"],
            "amount": 40,
            "expense_date": today,
            "payment_mode": "online",
            "online_payment_type": "upi",
        },
    )
    assert missing_txn.status_code == 422

    created = client.post(
        "/api/v1/expenses",
        headers=headers,
        json={
            "category_id": food["id"],
            "amount": 80,
            "expense_date": today,
            "payment_mode": "online",
            "transaction_id": "UPI123",
            "online_payment_type": "upi",
        },
    )
    assert created.status_code == 201
    body = created.json()
    assert body["payment_mode"] == "online"
    assert body["transaction_id"] == "UPI123"
    assert body["online_payment_type"] == "upi"

    cleared = client.patch(
        f"/api/v1/expenses/{body['id']}",
        headers=headers,
        json={"payment_mode": "cash"},
    )
    assert cleared.status_code == 200
    assert cleared.json()["payment_mode"] == "cash"
    assert cleared.json()["transaction_id"] is None
    assert cleared.json()["online_payment_type"] is None

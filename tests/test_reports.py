from datetime import date


def test_reports_and_summary(client):
    # Seed categories
    seed_res = client.post("/api/v1/categories/seed")
    categories = seed_res.json()
    food_cat = next(c for c in categories if c["name_key"] == "food")
    travel_cat = next(c for c in categories if c["name_key"] == "travel")

    # Register user
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": "reports_test@example.com", "password": "Password123!"},
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Set opening balance to 5000.00
    client.patch(
        "/api/v1/users/me/settings",
        headers=headers,
        json={"opening_balance": 5000.00},
    )

    today = date.today()

    # Add 2 expenses
    client.post(
        "/api/v1/expenses",
        headers=headers,
        json={
            "category_id": food_cat["id"],
            "amount": 500.00,
            "expense_date": str(today),
            "description": "Groceries",
        },
    )
    client.post(
        "/api/v1/expenses",
        headers=headers,
        json={
            "category_id": travel_cat["id"],
            "amount": 200.00,
            "expense_date": str(today),
            "description": "Metro card recharge",
        },
    )

    # 1. Summary Report
    summary_res = client.get("/api/v1/reports/summary", headers=headers)
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert summary["opening_balance"] == 5000.00
    assert summary["total_expense"] == 700.00
    assert summary["remaining_balance"] == 4300.00
    assert summary["today_expense"] == 700.00
    assert len(summary["category_summary"]) == 2

    # 2. Daily Report
    daily_res = client.get(
        f"/api/v1/reports/daily?year={today.year}&month={today.month}",
        headers=headers,
    )
    assert daily_res.status_code == 200
    assert len(daily_res.json()) >= 1
    assert daily_res.json()[0]["total_amount"] == 700.00

    # 3. Monthly Report
    monthly_res = client.get(
        f"/api/v1/reports/monthly?year={today.year}",
        headers=headers,
    )
    assert monthly_res.status_code == 200
    assert len(monthly_res.json()) >= 1

    # 4. Yearly Report
    yearly_res = client.get(
        f"/api/v1/reports/yearly?start_year={today.year}&end_year={today.year}",
        headers=headers,
    )
    assert yearly_res.status_code == 200
    assert len(yearly_res.json()) >= 1

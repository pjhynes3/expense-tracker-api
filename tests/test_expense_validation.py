from decimal import Decimal

import pytest

from app.database import SessionLocal
from app.db_models import ExpenseRow


def create_authenticated_headers(client) -> dict:
    registration_response = client.post(
        "/register",
        json={
            "email": "validation-user@example.com",
            "password": "password123",
        },
    )

    assert registration_response.status_code == 201

    login_response = client.post(
        "/login",
        json={
            "email": "validation-user@example.com",
            "password": "password123",
        },
    )

    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]

    return {
        "Authorization": f"Bearer {access_token}",
    }

@pytest.mark.parametrize(
    "invalid_amount",
    [
        0,
        -10.50,
    ],
)

def test_non_positive_amount_returns_bad_request(
    client,
    invalid_amount,
):
    headers = create_authenticated_headers(client)

    response = client.post(
        "/expenses",
        headers=headers,
        json={
            "description": "Invalid expense",
            "amount": invalid_amount,
            "category": "food",
            "merchant": "Test Merchant",
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Amount must be greater than 0.00"

    # Confirm the invalid expense was never stored.
    list_response = client.get(
        "/expenses",
        headers=headers,
    )

    assert list_response.status_code == 200
    assert list_response.json() == []

def test_invalid_category_returns_unprocessable_entity(client):
    headers = create_authenticated_headers(client)

    response = client.post(
        "/expenses",
        headers=headers,
        json={
            "description": "Invalid category expense",
            "amount": 10.00,
            "category": "spaceships",           # Pydantic should reject this because spaceships is not an ExpenseCategory enum val
            "merchant": "Test Merchant",
        },
    )

    assert response.status_code == 422

    list_response = client.get(
        "/expenses",
        headers=headers,
    )

    assert list_response.status_code == 200
    assert list_response.json() == []

def test_missing_required_field_returns_unprocessable_entity(client):
    headers = create_authenticated_headers(client)

    response = client.post(
        "/expenses",
        headers=headers,
        json={
            "amount": 10.00,
            "category": "food",
            "merchant": "Test Merchant",
        },
    )

    assert response.status_code == 422

def test_valid_expense_returns_created(client):
    headers = create_authenticated_headers(client)

    response = client.post(
        "/expenses",
        headers=headers,
        json={
            "description": "Valid lunch",
            "amount": 16.75,
            "category": "food",
            "merchant": "Test Restaurant",
        },
    )

    assert response.status_code == 201

    expense = response.json()

    assert "id" in expense
    assert expense["description"] == "Valid lunch"
    assert expense["amount"] == "16.75"
    assert expense["category"] == "food"
    assert expense["merchant"] == "Test Restaurant"
    assert "created_at" in expense
    assert "updated_at" in expense

def test_expense_amount_is_stored_as_exact_decimal(client):
    headers = create_authenticated_headers(client)

    response = client.post(
        "/expenses",
        headers=headers,
        json={
            "description": "Exact decimal expense",
            "amount": 0.10,
            "category": "food",
            "merchant": "Decimal Store",
        },
    )

    assert response.status_code == 201

    expense = response.json()
    expense_id = expense["id"]

    # The API preserves exact money by serializing Decimal as a string.
    assert expense["amount"] == "0.10"

    # PostgreSQL NUMERIC is returned through SQLAlchemy as Python Decimal.
    with SessionLocal() as db:
        stored_amount = (
            db.query(ExpenseRow.amount)
            .filter(ExpenseRow.id == expense_id)
            .scalar()
        )

    assert isinstance(stored_amount, Decimal)
    assert stored_amount == Decimal("0.10")
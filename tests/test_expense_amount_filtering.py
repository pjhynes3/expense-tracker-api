from datetime import UTC, datetime

import pytest

from app.database import SessionLocal
from app.db_models import ExpenseRow


def create_authenticated_headers(
    client,
    email: str = "amount-filter-user@example.com",
) -> dict[str, str]:
    password = "password123"

    registration_response = client.post(
        "/register",
        json={
            "email": email,
            "password": password,
        },
    )
    assert registration_response.status_code == 201

    login_response = client.post(
        "/login",
        json={
            "email": email,
            "password": password,
        },
    )
    assert login_response.status_code == 200

    return {
        "Authorization": f"Bearer {login_response.json()['access_token']}",
    }


def create_expense(
    client,
    headers: dict[str, str],
    description: str,
    amount: str,
    category: str = "food",
) -> str:
    response = client.post(
        "/expenses",
        headers=headers,
        json={
            "description": description,
            "amount": amount,
            "category": category,
            "merchant": "Amount Test Store",
        },
    )

    assert response.status_code == 201
    return response.json()["id"]


def set_expense_created_at(
    expense_id: str,
    created_at: datetime,
) -> None:
    with SessionLocal() as db:
        expense_row = db.query(ExpenseRow).filter(ExpenseRow.id == expense_id).one()
        expense_row.created_at = created_at
        db.commit()


def test_amount_range_includes_both_boundaries(client):
    headers = create_authenticated_headers(client)

    create_expense(
        client,
        headers,
        "Below amount range",
        "9.99",
    )
    minimum_boundary_id = create_expense(
        client,
        headers,
        "At minimum amount",
        "10.00",
    )
    maximum_boundary_id = create_expense(
        client,
        headers,
        "At maximum amount",
        "20.00",
    )
    create_expense(
        client,
        headers,
        "Above amount range",
        "20.01",
    )

    response = client.get(
        "/expenses",
        headers=headers,
        params={
            "min_amount": "10.00",
            "max_amount": "20.00",
        },
    )

    assert response.status_code == 200, response.json()

    response_data = response.json()
    returned_ids = {expense["id"] for expense in response_data["items"]}

    assert returned_ids == {
        minimum_boundary_id,
        maximum_boundary_id,
    }
    assert response_data["total"] == 2
    assert response_data["pages"] == 1


def test_min_amount_alone_excludes_only_lower_amounts(client):
    headers = create_authenticated_headers(client)

    create_expense(
        client,
        headers,
        "Below minimum",
        "9.99",
    )
    at_minimum_id = create_expense(
        client,
        headers,
        "At minimum",
        "10.00",
    )
    above_minimum_id = create_expense(
        client,
        headers,
        "Above minimum",
        "25.00",
    )

    response = client.get(
        "/expenses",
        headers=headers,
        params={"min_amount": "10.00"},
    )

    assert response.status_code == 200, response.json()

    response_data = response.json()
    returned_ids = {expense["id"] for expense in response_data["items"]}

    assert returned_ids == {
        at_minimum_id,
        above_minimum_id,
    }
    assert response_data["total"] == 2


def test_max_amount_alone_excludes_only_higher_amounts(client):
    headers = create_authenticated_headers(client)

    below_maximum_id = create_expense(
        client,
        headers,
        "Below maximum",
        "5.00",
    )
    at_maximum_id = create_expense(
        client,
        headers,
        "At maximum",
        "20.00",
    )
    create_expense(
        client,
        headers,
        "Above maximum",
        "20.01",
    )

    response = client.get(
        "/expenses",
        headers=headers,
        params={"max_amount": "20.00"},
    )

    assert response.status_code == 200, response.json()

    response_data = response.json()
    returned_ids = {expense["id"] for expense in response_data["items"]}

    assert returned_ids == {
        below_maximum_id,
        at_maximum_id,
    }
    assert response_data["total"] == 2


def test_reversed_amount_range_is_rejected(client):
    headers = create_authenticated_headers(client)

    response = client.get(
        "/expenses",
        headers=headers,
        params={
            "min_amount": "50.00",
            "max_amount": "10.00",
        },
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "min_amount must be less than or equal to max_amount"
    }


@pytest.mark.parametrize(
    "params",
    [
        {"min_amount": "not-a-number"},
        {"min_amount": "-0.01"},
        {"max_amount": "10.001"},
    ],
)
def test_invalid_amount_parameters_are_rejected(client, params):
    headers = create_authenticated_headers(client)

    response = client.get(
        "/expenses",
        headers=headers,
        params=params,
    )

    assert response.status_code == 422


def test_amount_filter_composes_with_other_filters_and_pagination(client):
    user_a_headers = create_authenticated_headers(
        client,
        "amount-composition-a@example.com",
    )
    user_b_headers = create_authenticated_headers(
        client,
        "amount-composition-b@example.com",
    )

    # These three satisfy every filter for User A.
    oldest_matching_id = create_expense(
        client,
        user_a_headers,
        "Oldest matching expense",
        "10.00",
    )
    middle_matching_id = create_expense(
        client,
        user_a_headers,
        "Middle matching expense",
        "20.00",
    )
    newest_matching_id = create_expense(
        client,
        user_a_headers,
        "Newest matching expense",
        "30.00",
    )

    # Each of these fails one part of the complete filter.
    below_amount_id = create_expense(
        client,
        user_a_headers,
        "Below amount range",
        "9.99",
    )
    above_amount_id = create_expense(
        client,
        user_a_headers,
        "Above amount range",
        "30.01",
    )
    wrong_category_id = create_expense(
        client,
        user_a_headers,
        "Wrong category",
        "20.00",
        category="transportation",
    )
    outside_date_id = create_expense(
        client,
        user_a_headers,
        "Outside date range",
        "20.00",
    )
    other_user_id = create_expense(
        client,
        user_b_headers,
        "Other user's matching expense",
        "20.00",
    )

    set_expense_created_at(
        oldest_matching_id,
        datetime(2026, 8, 10, 12, 0, tzinfo=UTC),
    )
    set_expense_created_at(
        middle_matching_id,
        datetime(2026, 8, 20, 12, 0, tzinfo=UTC),
    )
    set_expense_created_at(
        newest_matching_id,
        datetime(2026, 8, 30, 12, 0, tzinfo=UTC),
    )
    set_expense_created_at(
        below_amount_id,
        datetime(2026, 8, 15, 12, 0, tzinfo=UTC),
    )
    set_expense_created_at(
        above_amount_id,
        datetime(2026, 8, 16, 12, 0, tzinfo=UTC),
    )
    set_expense_created_at(
        wrong_category_id,
        datetime(2026, 8, 17, 12, 0, tzinfo=UTC),
    )
    set_expense_created_at(
        outside_date_id,
        datetime(2026, 7, 31, 12, 0, tzinfo=UTC),
    )
    set_expense_created_at(
        other_user_id,
        datetime(2026, 8, 25, 12, 0, tzinfo=UTC),
    )

    response = client.get(
        "/expenses",
        headers=user_a_headers,
        params={
            "category": "food",
            "start_date": "2026-08-01",
            "end_date": "2026-08-31",
            "min_amount": "10.00",
            "max_amount": "30.00",
            "page": 2,
            "page_size": 2,
        },
    )

    assert response.status_code == 200, response.json()

    response_data = response.json()
    returned_ids = [expense["id"] for expense in response_data["items"]]

    assert returned_ids == [oldest_matching_id]
    assert response_data["total"] == 3
    assert response_data["page"] == 2
    assert response_data["page_size"] == 2
    assert response_data["pages"] == 2

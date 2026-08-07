from datetime import UTC, datetime

from app.database import SessionLocal
from app.db_models import ExpenseRow


def create_authenticated_headers(
    client,
    email: str = "merchant-search-user@example.com",
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
    merchant: str | None,
    amount: str = "10.00",
    category: str = "food",
) -> str:
    response = client.post(
        "/expenses",
        headers=headers,
        json={
            "description": description,
            "amount": amount,
            "category": category,
            "merchant": merchant,
        },
    )

    assert response.status_code == 201
    return response.json()["id"]


def set_expense_created_at(
    expense_id: str,
    created_at: datetime,
) -> None:
    with SessionLocal() as session:
        expense = session.get(ExpenseRow, expense_id)
        assert expense is not None

        expense.created_at = created_at
        session.commit()


def test_merchant_search_is_partial_and_case_insensitive(client):
    headers = create_authenticated_headers(client)

    first_matching_id = create_expense(
        client,
        headers,
        "First matching merchant",
        "Trader Joe's",
    )
    second_matching_id = create_expense(
        client,
        headers,
        "Second matching merchant",
        "Neighborhood Trader Market",
    )

    create_expense(
        client,
        headers,
        "Different merchant",
        "Target",
    )
    create_expense(
        client,
        headers,
        "Missing merchant",
        None,
    )

    response = client.get(
        "/expenses",
        headers=headers,
        params={"merchant": "TrAdEr"},
    )

    assert response.status_code == 200, response.json()

    response_data = response.json()
    returned_ids = {expense["id"] for expense in response_data["items"]}

    assert returned_ids == {
        first_matching_id,
        second_matching_id,
    }
    assert response_data["total"] == 2
    assert response_data["pages"] == 1


def test_merchant_search_strips_surrounding_whitespace(client):
    headers = create_authenticated_headers(client)

    matching_id = create_expense(
        client,
        headers,
        "Matching merchant",
        "Trader Joe's",
    )
    create_expense(
        client,
        headers,
        "Different merchant",
        "Target",
    )

    response = client.get(
        "/expenses",
        headers=headers,
        params={"merchant": "   tRaDeR   "},
    )

    assert response.status_code == 200, response.json()

    response_data = response.json()
    returned_ids = {expense["id"] for expense in response_data["items"]}

    assert returned_ids == {matching_id}
    assert response_data["total"] == 1


def test_whitespace_only_merchant_search_is_rejected(client):
    headers = create_authenticated_headers(client)

    response = client.get(
        "/expenses",
        headers=headers,
        params={"merchant": "   "},
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "merchant must not be blank"}


def test_empty_merchant_search_is_rejected(client):
    headers = create_authenticated_headers(client)

    response = client.get(
        "/expenses",
        headers=headers,
        params={"merchant": ""},
    )

    assert response.status_code == 422


def test_merchant_search_composes_with_all_filters_and_pagination(client):
    user_a_headers = create_authenticated_headers(
        client,
        "merchant-composition-a@example.com",
    )
    user_b_headers = create_authenticated_headers(
        client,
        "merchant-composition-b@example.com",
    )

    # These three satisfy every filter for User A.
    oldest_matching_id = create_expense(
        client,
        user_a_headers,
        "Oldest matching expense",
        "Trader Joe's",
        amount="10.00",
    )
    middle_matching_id = create_expense(
        client,
        user_a_headers,
        "Middle matching expense",
        "Neighborhood Trader Market",
        amount="20.00",
    )
    newest_matching_id = create_expense(
        client,
        user_a_headers,
        "Newest matching expense",
        "TRADER EXPRESS",
        amount="30.00",
    )

    # Each expense below fails at least one required condition.
    wrong_merchant_id = create_expense(
        client,
        user_a_headers,
        "Wrong merchant",
        "Target",
        amount="20.00",
    )
    below_amount_id = create_expense(
        client,
        user_a_headers,
        "Below amount range",
        "Trader Market",
        amount="9.99",
    )
    wrong_category_id = create_expense(
        client,
        user_a_headers,
        "Wrong category",
        "Trader Market",
        amount="20.00",
        category="transportation",
    )
    outside_date_id = create_expense(
        client,
        user_a_headers,
        "Outside date range",
        "Trader Market",
        amount="20.00",
    )
    other_user_id = create_expense(
        client,
        user_b_headers,
        "Other user's matching expense",
        "Trader Market",
        amount="20.00",
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
        wrong_merchant_id,
        datetime(2026, 8, 15, 12, 0, tzinfo=UTC),
    )
    set_expense_created_at(
        below_amount_id,
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
            "merchant": "tRaDeR",
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

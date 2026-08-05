from datetime import UTC, datetime

from app.database import SessionLocal
from app.db_models import ExpenseRow


def create_authenticated_headers(
    client, email: str = "date-filter-user@example.com"
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
    category: str = "food",
) -> str:
    response = client.post(
        "/expenses",
        headers=headers,
        json={
            "description": description,
            "amount": "10.00",
            "category": category,
            "merchant": "Date Test Store",
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


def test_date_range_includes_both_calendar_date_boundaries(client):
    headers = create_authenticated_headers(client)

    before_range_id = create_expense(client, headers, "Before range")
    start_boundary_id = create_expense(client, headers, "Start boundary")
    late_end_date_id = create_expense(client, headers, "Late on end date")
    after_range_id = create_expense(client, headers, "After range")

    set_expense_created_at(
        before_range_id,
        datetime(2026, 7, 31, 23, 59, 59, tzinfo=UTC),
    )
    set_expense_created_at(
        start_boundary_id,
        datetime(2026, 8, 1, 0, 0, tzinfo=UTC),
    )
    set_expense_created_at(
        late_end_date_id,
        datetime(2026, 8, 31, 23, 59, 59, 999999, tzinfo=UTC),
    )
    set_expense_created_at(
        after_range_id,
        datetime(2026, 9, 1, 0, 0, tzinfo=UTC),
    )

    response = client.get(
        "/expenses",
        headers=headers,
        params={
            "start_date": "2026-08-01",
            "end_date": "2026-08-31",
        },
    )

    assert response.status_code == 200

    response_data = response.json()
    returned_ids = {expense["id"] for expense in response_data["items"]}

    assert returned_ids == {
        start_boundary_id,
        late_end_date_id,
    }
    assert response_data["total"] == 2
    assert response_data["pages"] == 1


def test_start_date_alone_excludes_only_earlier_expenses(client):
    headers = create_authenticated_headers(client)

    before_start_id = create_expense(client, headers, "Before start date")
    at_start_id = create_expense(client, headers, "At start date")
    after_start_id = create_expense(client, headers, "After start date")

    set_expense_created_at(
        before_start_id,
        datetime(2026, 7, 31, 23, 59, 59, tzinfo=UTC),
    )
    set_expense_created_at(
        at_start_id,
        datetime(2026, 8, 1, 0, 0, tzinfo=UTC),
    )
    set_expense_created_at(
        after_start_id,
        datetime(2026, 9, 1, 12, 0, tzinfo=UTC),
    )

    response = client.get(
        "/expenses",
        headers=headers,
        params={"start_date": "2026-08-01"},
    )

    assert response.status_code == 200

    response_data = response.json()
    returned_ids = {expense["id"] for expense in response_data["items"]}

    assert returned_ids == {
        at_start_id,
        after_start_id,
    }
    assert response_data["total"] == 2


def test_end_date_alone_excludes_only_later_expenses(client):
    headers = create_authenticated_headers(client)

    before_end_id = create_expense(client, headers, "Before end date")
    late_end_date_id = create_expense(client, headers, "Late on end date")
    after_end_id = create_expense(client, headers, "After end date")

    set_expense_created_at(
        before_end_id,
        datetime(2026, 7, 1, 12, 0, tzinfo=UTC),
    )
    set_expense_created_at(
        late_end_date_id,
        datetime(2026, 8, 31, 23, 59, 59, 999999, tzinfo=UTC),
    )
    set_expense_created_at(
        after_end_id,
        datetime(2026, 9, 1, 0, 0, tzinfo=UTC),
    )

    response = client.get(
        "/expenses",
        headers=headers,
        params={"end_date": "2026-08-31"},
    )

    assert response.status_code == 200

    response_data = response.json()
    returned_ids = {expense["id"] for expense in response_data["items"]}

    assert returned_ids == {
        before_end_id,
        late_end_date_id,
    }
    assert response_data["total"] == 2


def test_reversed_date_range_is_rejected(client):
    headers = create_authenticated_headers(client)

    response = client.get(
        "/expenses",
        headers=headers,
        params={
            "start_date": "2026-09-01",
            "end_date": "2026-08-31",
        },
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "start_date must be on or before end_date"}


def test_date_filter_composes_with_ownership_category_and_pagination(client):
    user_a_headers = create_authenticated_headers(
        client,
        "date-composition-a@example.com",
    )
    user_b_headers = create_authenticated_headers(
        client,
        "date-composition-b@example.com",
    )

    # These three expenses should match User A's complete filter.
    user_a_oldest_matching_id = create_expense(
        client,
        user_a_headers,
        "User A August food 1",
    )
    user_a_middle_matching_id = create_expense(
        client,
        user_a_headers,
        "User A August food 2",
    )
    user_a_newest_matching_id = create_expense(
        client,
        user_a_headers,
        "User A August food 3",
    )

    # These expenses each fail one part of the complete filter.
    user_a_outside_range_id = create_expense(
        client,
        user_a_headers,
        "User A July food",
    )
    user_a_wrong_category_id = create_expense(
        client,
        user_a_headers,
        "User A August transportation",
        category="transportation",
    )
    user_b_matching_filter_id = create_expense(
        client,
        user_b_headers,
        "User B August food",
    )

    set_expense_created_at(
        user_a_oldest_matching_id,
        datetime(2026, 8, 10, 12, 0, tzinfo=UTC),
    )
    set_expense_created_at(
        user_a_middle_matching_id,
        datetime(2026, 8, 20, 12, 0, tzinfo=UTC),
    )
    set_expense_created_at(
        user_a_newest_matching_id,
        datetime(2026, 8, 30, 12, 0, tzinfo=UTC),
    )
    set_expense_created_at(
        user_a_outside_range_id,
        datetime(2026, 7, 31, 12, 0, tzinfo=UTC),
    )
    set_expense_created_at(
        user_a_wrong_category_id,
        datetime(2026, 8, 15, 12, 0, tzinfo=UTC),
    )
    set_expense_created_at(
        user_b_matching_filter_id,
        datetime(2026, 8, 25, 12, 0, tzinfo=UTC),
    )

    response = client.get(
        "/expenses",
        headers=user_a_headers,
        params={
            "category": "food",
            "start_date": "2026-08-01",
            "end_date": "2026-08-31",
            "page": 2,
            "page_size": 2,
        },
    )

    assert response.status_code == 200

    response_data = response.json()
    returned_ids = [expense["id"] for expense in response_data["items"]]

    assert returned_ids == [user_a_oldest_matching_id]
    assert response_data["total"] == 3
    assert response_data["page"] == 2
    assert response_data["page_size"] == 2
    assert response_data["pages"] == 2

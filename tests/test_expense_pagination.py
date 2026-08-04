import pytest


def create_authenticated_headers(client) -> dict[str, str]:
    email = "pagination-user@example.com"
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
) -> str:
    response = client.post(
        "/expenses",
        headers=headers,
        json={
            "description": description,
            "amount": "10.00",
            "category": "food",
            "merchant": "Pagination Store",
        },
    )

    assert response.status_code == 201
    return response.json()["id"]


def test_expenses_are_split_across_pages(client):
    headers = create_authenticated_headers(client)

    created_ids = {
        create_expense(client, headers, f"Expense {number}") for number in range(1, 6)
    }

    page_one_response = client.get(
        "/expenses",
        headers=headers,
        params={"page": 1, "page_size": 2},
    )
    page_two_response = client.get(
        "/expenses",
        headers=headers,
        params={"page": 2, "page_size": 2},
    )
    page_three_response = client.get(
        "/expenses",
        headers=headers,
        params={"page": 3, "page_size": 2},
    )

    assert page_one_response.status_code == 200
    assert page_two_response.status_code == 200
    assert page_three_response.status_code == 200

    page_one = page_one_response.json()
    page_two = page_two_response.json()
    page_three = page_three_response.json()

    assert page_one["total"] == 5
    assert page_one["page"] == 1
    assert page_one["page_size"] == 2
    assert page_one["pages"] == 3

    assert len(page_one["items"]) == 2
    assert len(page_two["items"]) == 2
    assert len(page_three["items"]) == 1

    returned_ids = {
        expense["id"]
        for page in (page_one, page_two, page_three)
        for expense in page["items"]
    }

    assert returned_ids == created_ids


@pytest.mark.parametrize(
    "params",
    [
        {"page": 0, "page_size": 20},
        {"page": 1, "page_size": 0},
        {"page": 1, "page_size": 101},
    ],
)
def test_invalid_pagination_parameters_are_rejected(client, params):
    headers = create_authenticated_headers(client)

    response = client.get(
        "/expenses",
        headers=headers,
        params=params,
    )

    assert response.status_code == 422

def register_user(
        client,
        email: str,
        password: str = "password123"
) -> None:
    response = client.post(
        "/register",
        json={
            "email":email,
            "password":password,
        },
    )

    assert response.status_code == 201

def login_user(
        client,
        email: str,
        password: str = "password123",
) -> str:
    response = client.post(
        "/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200
    return response.json()["access_token"]

def authorization_header(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
    }

def test_user_cannot_access_another_users_expense(client):
    # Arrange: create and authenticate two separate users.
    register_user(client, "user-a@example.com")
    register_user(client, "user-b@example.com")

    user_a_token = login_user(client, "user-a@example.com")
    user_b_token = login_user(client, "user-b@example.com")

    # Act: User A creates an expense.
    create_response = client.post(
        "/expenses",
        headers=authorization_header(user_a_token),
        json={
            "description": "User A lunch",
            "amount": 18.50,
            "category": "food",
            "merchant": "Test Restaurant",
        },
    )

    assert create_response.status_code == 201

    expense_id = create_response.json()["id"]

    # Assert: User A can retrieve their own expense.
    owner_response = client.get(
        f"/expenses/{expense_id}",
        headers=authorization_header(user_a_token),
    )

    assert owner_response.status_code == 200
    assert owner_response.json()["id"] == expense_id

    # Assert: User B cannot retrieve User A's expense.
    other_user_response = client.get(
        f"/expenses/{expense_id}",
        headers=authorization_header(user_b_token),
    )

    assert other_user_response.status_code == 404
    assert other_user_response.json()["detail"] == "Expense not found"
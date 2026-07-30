def register_user(client, email: str, password: str = "password123") -> None:
    response = client.post(
        "/register",
        json={
            "email": email,
            "password": password,
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


def test_users_only_list_their_own_expenses(client):
    # Arrange: create and authenticate two users.
    register_user(client, "user-a@example.com")
    register_user(client, "user-b@example.com")

    user_a_token = login_user(client, "user-a@example.com")
    user_b_token = login_user(client, "user-b@example.com")

    # Each user creates one expense.
    user_a_create_response = client.post(
        "/expenses",
        headers=authorization_header(user_a_token),
        json={
            "description": "User A lunch",
            "amount": 15.00,
            "category": "food",
            "merchant": "Restaurant A",
        },
    )

    user_b_create_response = client.post(
        "/expenses",
        headers=authorization_header(user_b_token),
        json={
            "description": "User B train ticket",
            "amount": 8.00,
            "category": "transportation",
            "merchant": "Transit",
        },
    )

    assert user_a_create_response.status_code == 201
    assert user_b_create_response.status_code == 201

    user_a_expense_id = user_a_create_response.json()["id"]
    user_b_expense_id = user_b_create_response.json()["id"]

    # Act: each user requests their expense list.
    user_a_list_response = client.get(
        "/expenses",
        headers=authorization_header(user_a_token),
    )

    user_b_list_response = client.get(
        "/expenses",
        headers=authorization_header(user_b_token),
    )

    assert user_a_list_response.status_code == 200
    assert user_b_list_response.status_code == 200

    # Assert: each response contains exactly that user's expense.
    user_a_returned_ids = {expense["id"] for expense in user_a_list_response.json()}

    user_b_returned_ids = {expense["id"] for expense in user_b_list_response.json()}

    assert user_a_returned_ids == {user_a_expense_id}
    assert user_b_returned_ids == {user_b_expense_id}


def test_user_cannot_update_another_users_expense(client):
    # Arrange: create and authenticate two users.
    register_user(client, "user-a@example.com")
    register_user(client, "user-b@example.com")

    user_a_token = login_user(client, "user-a@example.com")
    user_b_token = login_user(client, "user-b@example.com")

    # User A creates an expense.
    create_response = client.post(
        "/expenses",
        headers=authorization_header(user_a_token),
        json={
            "description": "Original description",
            "amount": 20.00,
            "category": "food",
            "merchant": "Original Restaurant",
        },
    )

    assert create_response.status_code == 201

    expense_id = create_response.json()["id"]

    # Retrieve it as User A so the original expense enters the cache.
    initial_get_response = client.get(
        f"/expenses/{expense_id}",
        headers=authorization_header(user_a_token),
    )

    assert initial_get_response.status_code == 200
    assert initial_get_response.json()["description"] == "Original description"

    # Act: User B attempts to update User A's expense.
    unauthorized_update_response = client.put(
        f"/expenses/{expense_id}",
        headers=authorization_header(user_b_token),
        json={
            "description": "Hacked by User B",
        },
    )

    # Assert: User B cannot update it.
    assert unauthorized_update_response.status_code == 404
    assert unauthorized_update_response.json()["detail"] == "Expense not found"

    # Confirm User B's failed attempt changed nothing.
    unchanged_get_response = client.get(
        f"/expenses/{expense_id}",
        headers=authorization_header(user_a_token),
    )

    assert unchanged_get_response.status_code == 200
    assert unchanged_get_response.json()["description"] == "Original description"

    # Act: User A updates their own expense.
    owner_update_response = client.put(
        f"/expenses/{expense_id}",
        headers=authorization_header(user_a_token),
        json={
            "description": "Updated by User A",
        },
    )

    assert owner_update_response.status_code == 200
    assert owner_update_response.json()["description"] == "Updated by User A"

    # Confirm a new GET returns the updated value, not the stale cached value.
    updated_get_response = client.get(
        f"/expenses/{expense_id}",
        headers=authorization_header(user_a_token),
    )

    assert updated_get_response.status_code == 200
    assert updated_get_response.json()["description"] == "Updated by User A"


def test_user_cannot_delete_another_users_expense(client):
    # Arrange: create and authenticate two users.
    register_user(client, "user-a@example.com")
    register_user(client, "user-b@example.com")

    user_a_token = login_user(client, "user-a@example.com")
    user_b_token = login_user(client, "user-b@example.com")

    # User A creates an expense.
    create_response = client.post(
        "/expenses",
        headers=authorization_header(user_a_token),
        json={
            "description": "Expense to delete",
            "amount": 25.00,
            "category": "entertainment",
            "merchant": "Test Merchant",
        },
    )

    assert create_response.status_code == 201

    expense_id = create_response.json()["id"]

    # Retrieve it as User A so the expense enters the cache.
    initial_get_response = client.get(
        f"/expenses/{expense_id}",
        headers=authorization_header(user_a_token),
    )

    assert initial_get_response.status_code == 200

    # Act: User B attempts to delete User A's expense.
    unauthorized_delete_response = client.delete(
        f"/expenses/{expense_id}",
        headers=authorization_header(user_b_token),
    )

    # Assert: User B cannot delete it.
    assert unauthorized_delete_response.status_code == 404
    assert unauthorized_delete_response.json()["detail"] == "Expense not found"

    # Confirm the expense still exists for User A.
    still_exists_response = client.get(
        f"/expenses/{expense_id}",
        headers=authorization_header(user_a_token),
    )

    assert still_exists_response.status_code == 200
    assert still_exists_response.json()["id"] == expense_id

    # Act: User A deletes their own expense.
    owner_delete_response = client.delete(
        f"/expenses/{expense_id}",
        headers=authorization_header(user_a_token),
    )

    assert owner_delete_response.status_code == 200
    assert owner_delete_response.json() == {"message": "Expense deleted successfully"}

    # Confirm it is gone and its cached copy was removed.
    deleted_get_response = client.get(
        f"/expenses/{expense_id}",
        headers=authorization_header(user_a_token),
    )

    assert deleted_get_response.status_code == 404
    assert deleted_get_response.json()["detail"] == "Expense not found"


def test_category_filter_only_returns_current_users_matching_expenses(client):
    # Arrange: create and authenticate two users.
    register_user(client, "user-a@example.com")
    register_user(client, "user-b@example.com")

    user_a_token = login_user(client, "user-a@example.com")
    user_b_token = login_user(client, "user-b@example.com")

    # User A creates one food expense and one transportation expense.
    user_a_food_response = client.post(
        "/expenses",
        headers=authorization_header(user_a_token),
        json={
            "description": "User A lunch",
            "amount": 15.00,
            "category": "food",
            "merchant": "Restaurant A",
        },
    )

    user_a_transportation_response = client.post(
        "/expenses",
        headers=authorization_header(user_a_token),
        json={
            "description": "User A train ticket",
            "amount": 8.00,
            "category": "transportation",
            "merchant": "Transit",
        },
    )

    # User B also creates a food expense.
    user_b_food_response = client.post(
        "/expenses",
        headers=authorization_header(user_b_token),
        json={
            "description": "User B dinner",
            "amount": 25.00,
            "category": "food",
            "merchant": "Restaurant B",
        },
    )

    assert user_a_food_response.status_code == 201
    assert user_a_transportation_response.status_code == 201
    assert user_b_food_response.status_code == 201

    user_a_food_id = user_a_food_response.json()["id"]

    # Act: User A requests only their food expenses.
    response = client.get(
        "/expenses",
        headers=authorization_header(user_a_token),
        params={"category": "food"},
    )

    # Assert: only User A's matching food expense is returned.
    assert response.status_code == 200

    returned_expenses = response.json()
    returned_ids = {expense["id"] for expense in returned_expenses}

    assert returned_ids == {user_a_food_id}
    assert all(expense["category"] == "food" for expense in returned_expenses)

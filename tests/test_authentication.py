import pytest

def test_user_can_register_login_and_access_me(client):
     # Arrange/Act: register a new user.
    registration_response = client.post(
        "/register",
        json={
            "email": "authenticated-user@example.com",
            "password": "password123",
        },
    )

    # Assert: registration succeeded and returned a safe response.
    assert registration_response.status_code == 201

    registered_user = registration_response.json()
    assert registered_user["email"] == "authenticated-user@example.com"
    assert "id" in registered_user
    assert "created_at" in registered_user
    assert "password" not in registered_user
    assert "hashed_password" not in registered_user

    # Act: log in with the registered credentials.
    login_response = client.post(
        "/login",
        json={
            "email": "authenticated-user@example.com",
            "password": "password123",
        },
    )

    # Assert: login returned a bearer token.
    assert login_response.status_code == 200

    login_data = login_response.json()

    assert "access_token" in login_data
    assert login_data["token_type"] == "bearer"

    access_token = login_data["access_token"]

    # Act: use the JWT to ask the API who we are.
    me_response = client.get(
        "/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    # Assert: /me returns the authenticated user.
    assert me_response.status_code == 200

    current_user = me_response.json()

    assert current_user["id"] == registered_user["id"]
    assert current_user["email"] == registered_user["email"]
    assert "password" not in current_user
    assert "hashed_password" not in current_user

def test_duplicate_registration_returns_bad_request(client):
    user_data = {
        "email": "duplicate-user@example.com",
        "password": "password123",
    }

    # First registration succeeds.
    first_response = client.post(
        "/register",
        json=user_data,
    )

    assert first_response.status_code == 201

    # Registering the same email again fails.
    duplicate_response = client.post(
        "/register",
        json=user_data,
    )

    assert duplicate_response.status_code == 400
    assert duplicate_response.json()["detail"] == "Email is already registered"

@pytest.mark.parametrize(
    "login_email, login_password",
    [
        ("valid-user@example.com", "wrong-password"),
        ("unknown-user@example.com", "password123"),
    ]
)

def test_invalid_login_returns_unauthorized(
    client,
    login_email,
    login_password,
):
    # Arrange: create one legitimate user.
    registration_response = client.post(
        "/register",
        json={
            "email": "valid-user@example.com",
            "password": "password123",
        },
    )

    assert registration_response.status_code == 201

    # Act: attempt login with either a wrong password or unknown email.
    login_response = client.post(
        "/login",
        json={
            "email": login_email,
            "password": login_password,
        },
    )

    # Assert: both cases receive the same generic response.
    assert login_response.status_code == 401
    assert login_response.json()["detail"] == "Invalid email or password"
    assert "access_token" not in login_response.json()

def test_missing_token_is_rejected(client):
    resposne = client.get("/me")
    assert resposne.status_code == 401

def test_tampered_token_is_rejected(client):
    # Arrange: register and log in normally.
    registration_response = client.post(
        "/register",
        json={
            "email": "tampered-token-user@example.com",
            "password": "password123",
        },
    )

    assert registration_response.status_code == 201

    login_response = client.post(
        "/login",
        json={
            "email": "tampered-token-user@example.com",
            "password": "password123",
        },
    )

    assert login_response.status_code == 200

    valid_token = login_response.json()["access_token"]

    # Modify the payload without regenerating the signature.
    header, payload, signature = valid_token.split(".")

    replacement_character = "A" if payload[0] != "A" else "B"
    tampered_payload = replacement_character + payload[1:]

    tampered_token = (
        f"{header}.{tampered_payload}.{signature}"
    )

    # Act: submit the modified token.
    response = client.get(
        "/me",
        headers={
            "Authorization": f"Bearer {tampered_token}",
        },
    )

    # Assert: signature verification rejects it.
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"
import uuid

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def unique_email():
    return f"test_{uuid.uuid4().hex[:10]}@example.com"


def register_user(email: str, password: str = "TestPass123!"):
    return client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "Test User",
            "password": password,
        },
    )


def login_user(email: str, password: str = "TestPass123!"):
    return client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_register_user():
    email = unique_email()

    response = register_user(email)

    assert response.status_code == 201

    data = response.json()

    assert data["success"] is True
    assert data["data"]["email"] == email
    assert data["data"]["full_name"] == "Test User"
    assert data["data"]["role"] == "customer"
    assert data["data"]["status"] == "active"


def test_duplicate_email_registration():
    email = unique_email()

    first_response = register_user(email)

    assert first_response.status_code == 201

    second_response = register_user(email)

    assert second_response.status_code == 409

    data = second_response.json()

    assert data["success"] is False


def test_login_success():
    email = unique_email()

    register_response = register_user(email)

    assert register_response.status_code == 201

    response = login_user(email)

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]
    assert data["data"]["access_token"]
    assert data["data"]["refresh_token"]


def test_login_invalid_password():
    email = unique_email()

    register_response = register_user(email)

    assert register_response.status_code == 201

    response = login_user(
        email,
        "WrongPassword123!",
    )

    assert response.status_code == 401

    data = response.json()

    assert data["success"] is False


def test_login_unknown_email():
    email = unique_email()

    response = login_user(email)

    assert response.status_code == 401

    data = response.json()

    assert data["success"] is False


def test_current_user():
    email = unique_email()

    register_response = register_user(email)

    assert register_response.status_code == 201

    login_response = login_user(email)

    assert login_response.status_code == 200

    access_token = login_response.json()["data"]["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["data"]["email"] == email


def test_current_user_without_token():
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401

    data = response.json()

    assert data["success"] is False


def test_refresh_token():
    email = unique_email()

    register_response = register_user(email)

    assert register_response.status_code == 201

    login_response = login_user(email)

    assert login_response.status_code == 200

    refresh_token = login_response.json()["data"]["refresh_token"]

    response = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": refresh_token
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]


def test_logout():
    email = unique_email()

    register_response = register_user(email)

    assert register_response.status_code == 201

    login_response = login_user(email)

    assert login_response.status_code == 200

    login_data = login_response.json()["data"]

    access_token = login_data["access_token"]
    refresh_token = login_data["refresh_token"]

    response = client.post(
        "/api/v1/auth/logout",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
        json={
            "refresh_token": refresh_token
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True


def test_refresh_token_after_logout_is_rejected():
    email = unique_email()

    register_response = register_user(email)

    assert register_response.status_code == 201

    login_response = login_user(email)

    assert login_response.status_code == 200

    login_data = login_response.json()["data"]

    access_token = login_data["access_token"]
    refresh_token = login_data["refresh_token"]

    logout_response = client.post(
        "/api/v1/auth/logout",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
        json={
            "refresh_token": refresh_token
        },
    )

    assert logout_response.status_code == 200

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": refresh_token
        },
    )

    assert refresh_response.status_code == 401
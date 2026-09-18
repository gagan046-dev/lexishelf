from fastapi.testclient import TestClient
from jose import jwt
from sqlmodel import Session, select

from app.config.settings import get_settings
from app.models.user import User


def test_register_creates_hashed_user_and_returns_jwt(client: TestClient, session: Session) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": " Reader@Example.com ", "password": "long-enough-password"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["user"]["email"] == "reader@example.com"
    payload = jwt.decode(
        body["access_token"],
        get_settings().jwt_signing_secret,
        algorithms=[get_settings().jwt_algorithm],
    )
    assert payload["sub"] == body["user"]["id"]
    user = session.exec(select(User).where(User.email == "reader@example.com")).one()
    assert user.hashed_password != "long-enough-password"


def test_login_returns_token_for_valid_credentials(client: TestClient) -> None:
    credentials = {"email": "reader@example.com", "password": "long-enough-password"}
    client.post("/api/v1/auth/register", json=credentials)

    response = client.post("/api/v1/auth/login", json=credentials)

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"


def test_login_rejects_invalid_credentials(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "missing@example.com", "password": "long-enough-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"]["error_code"] == "INVALID_CREDENTIALS"


def test_register_rejects_duplicate_email(client: TestClient) -> None:
    credentials = {"email": "reader@example.com", "password": "long-enough-password"}
    client.post("/api/v1/auth/register", json=credentials)

    response = client.post("/api/v1/auth/register", json=credentials)

    assert response.status_code == 409
    assert response.json()["detail"]["error_code"] == "EMAIL_IN_USE"
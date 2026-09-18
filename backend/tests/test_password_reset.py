from fastapi.testclient import TestClient


def test_forgot_password_returns_generic_message_for_unknown_email(client: TestClient) -> None:
    response = client.post("/api/v1/auth/forgot-password", json={"email": "missing@example.com"})

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "If an account uses this email, a reset code has been sent."
    assert body["dev_reset_token"] is None


def test_forgot_password_issues_dev_token_that_resets_the_password(client: TestClient) -> None:
    credentials = {"email": "reader@example.com", "password": "original-password"}
    client.post("/api/v1/auth/register", json=credentials)

    forgot_response = client.post("/api/v1/auth/forgot-password", json={"email": credentials["email"]})
    assert forgot_response.status_code == 200
    reset_token = forgot_response.json()["dev_reset_token"]
    assert reset_token

    reset_response = client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token, "new_password": "brand-new-password"},
    )
    assert reset_response.status_code == 200
    assert reset_response.json()["token_type"] == "bearer"

    assert client.post("/api/v1/auth/login", json=credentials).status_code == 401
    new_login = client.post(
        "/api/v1/auth/login",
        json={"email": credentials["email"], "password": "brand-new-password"},
    )
    assert new_login.status_code == 200


def test_reset_password_rejects_invalid_token(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/reset-password",
        json={"token": "not-a-real-token", "new_password": "brand-new-password"},
    )

    assert response.status_code == 400
    assert response.json()["detail"]["error_code"] == "INVALID_RESET_TOKEN"


def test_reset_password_token_is_single_use(client: TestClient) -> None:
    credentials = {"email": "reader@example.com", "password": "original-password"}
    client.post("/api/v1/auth/register", json=credentials)
    reset_token = client.post(
        "/api/v1/auth/forgot-password", json={"email": credentials["email"]}
    ).json()["dev_reset_token"]

    first_attempt = client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token, "new_password": "brand-new-password"},
    )
    assert first_attempt.status_code == 200

    second_attempt = client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token, "new_password": "another-password"},
    )
    assert second_attempt.status_code == 400
    assert second_attempt.json()["detail"]["error_code"] == "INVALID_RESET_TOKEN"

from fastapi.testclient import TestClient


def test_login_is_rate_limited_after_repeated_attempts(client: TestClient) -> None:
    credentials = {"email": "missing@example.com", "password": "wrong-password"}

    for _ in range(10):
        response = client.post("/api/v1/auth/login", json=credentials)
        assert response.status_code == 401

    limited = client.post("/api/v1/auth/login", json=credentials)

    assert limited.status_code == 429
    assert limited.json()["detail"]["error_code"] == "RATE_LIMITED"


def test_forgot_password_is_rate_limited_after_repeated_attempts(client: TestClient) -> None:
    for _ in range(5):
        response = client.post("/api/v1/auth/forgot-password", json={"email": "someone@example.com"})
        assert response.status_code == 200

    limited = client.post("/api/v1/auth/forgot-password", json={"email": "someone@example.com"})

    assert limited.status_code == 429
    assert limited.json()["detail"]["error_code"] == "RATE_LIMITED"

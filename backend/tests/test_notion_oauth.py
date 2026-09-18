import base64
import json
from urllib.parse import parse_qs, urlparse

import httpx
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.api.routes.notion import get_notion_oauth_service
from app.config.settings import get_settings
from app.main import app
from app.models.notion_connection import NotionConnection
from app.security.notion_tokens import NotionTokenVault
from app.services.notion_oauth import NotionOAuthCredentials, NotionOAuthService


def test_oauth_exchange_uses_basic_auth_and_current_version():
    def handler(request: httpx.Request) -> httpx.Response:
        expected = base64.b64encode(b"client-id:client-secret").decode("ascii")
        assert request.headers["Authorization"] == f"Basic {expected}"
        assert request.headers["Notion-Version"] == "2026-03-11"
        assert json.loads(request.content) == {
            "grant_type": "authorization_code",
            "code": "temporary-code",
            "redirect_uri": "https://example.com/callback",
        }
        return httpx.Response(
            200,
            json={
                "access_token": "access-token",
                "refresh_token": "refresh-token",
                "workspace_id": "workspace-1",
                "workspace_name": "Reading Room",
            },
        )

    service = NotionOAuthService(transport=httpx.MockTransport(handler))

    credentials = service.exchange_code(
        "client-id",
        "client-secret",
        "temporary-code",
        "https://example.com/callback",
    )

    assert credentials.workspace_id == "workspace-1"


def test_oauth_callback_stores_tokens_encrypted_and_scoped_to_state_user(
    client: TestClient,
    session: Session,
    current_user: dict[str, str],
    monkeypatch,
) -> None:
    encryption_key = Fernet.generate_key().decode("ascii")
    settings = get_settings()
    monkeypatch.setattr(settings, "notion_client_id", "client-id")
    monkeypatch.setattr(settings, "notion_client_secret", "client-secret")
    monkeypatch.setattr(settings, "notion_redirect_uri", "https://example.com/callback")
    monkeypatch.setattr(settings, "notion_oauth_state_secret", "state-secret")
    monkeypatch.setattr(settings, "notion_token_encryption_key", encryption_key)

    class FakeOAuthService:
        def exchange_code(self, client_id, client_secret, code, redirect_uri):
            assert code == "temporary-code"
            return NotionOAuthCredentials(
                access_token="access-token",
                refresh_token="refresh-token",
                workspace_id="workspace-1",
                workspace_name="Reading Room",
            )

    app.dependency_overrides[get_notion_oauth_service] = lambda: FakeOAuthService()
    authorize_response = client.get("/api/v1/notion/oauth/authorize")
    authorization_url = authorize_response.json()["authorization_url"]
    state_token = parse_qs(urlparse(authorization_url).query)["state"][0]

    current_user["id"] = "different-current-user"
    callback_response = client.get(
        "/api/v1/notion/oauth/callback",
        params={"code": "temporary-code", "state": state_token},
    )

    assert callback_response.status_code == 200
    assert callback_response.headers["content-type"].startswith("text/html")
    assert "Notion connected" in callback_response.text
    assert 'postMessage({ type: "lexishelf:notion-connected" }, "*")' in callback_response.text
    assert "access-token" not in callback_response.text
    connection = session.exec(
        select(NotionConnection).where(NotionConnection.user_id == "user-a")
    ).one()
    assert connection.access_token_encrypted != "access-token"
    vault = NotionTokenVault(encryption_key)
    assert vault.decrypt(connection.access_token_encrypted) == "access-token"
    assert vault.decrypt(connection.refresh_token_encrypted or "") == "refresh-token"
    assert session.exec(
        select(NotionConnection).where(NotionConnection.user_id == "different-current-user")
    ).first() is None
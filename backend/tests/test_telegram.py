from fastapi.testclient import TestClient

from app.api.routes.chat import get_vocabulary_agent_runner
from app.config.settings import get_settings
from app.main import app
from app.schemas.chat import AgentAction, ChatResponse


class SuccessfulAgentRunner:
    def run(self, message, request_id, tools, collection_id=None):
        assert collection_id is None
        return ChatResponse(
            message=f"Explained: {message}",
            actions=[AgentAction(type="vocabulary_save", status="success", message="Saved.")],
            request_id=request_id,
        )


def _get_link_code(client: TestClient) -> str:
    response = client.get("/api/v1/telegram/link/code")
    assert response.status_code == 200
    return response.json()["code"]


def test_link_code_links_a_chat_to_the_authenticated_user(client: TestClient) -> None:
    code = _get_link_code(client)

    response = client.post(
        "/api/v1/telegram/webhook",
        json={"message": {"chat": {"id": 555}, "text": f"/link {code}"}},
    )

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_link_code_is_rejected_when_invalid(client: TestClient) -> None:
    response = client.post(
        "/api/v1/telegram/webhook",
        json={"message": {"chat": {"id": 555}, "text": "/link 000000"}},
    )

    assert response.status_code == 200


def test_message_from_unlinked_chat_does_not_reach_the_agent(client: TestClient) -> None:
    app.dependency_overrides[get_vocabulary_agent_runner] = lambda: SuccessfulAgentRunner()
    try:
        response = client.post(
            "/api/v1/telegram/webhook",
            json={"message": {"chat": {"id": 999}, "text": "Explain omen"}},
        )
        assert response.status_code == 200
    finally:
        app.dependency_overrides.pop(get_vocabulary_agent_runner, None)


def test_message_from_linked_chat_reaches_the_agent(client: TestClient) -> None:
    code = _get_link_code(client)
    client.post(
        "/api/v1/telegram/webhook",
        json={"message": {"chat": {"id": 777}, "text": f"/link {code}"}},
    )

    app.dependency_overrides[get_vocabulary_agent_runner] = lambda: SuccessfulAgentRunner()
    try:
        response = client.post(
            "/api/v1/telegram/webhook",
            json={"message": {"chat": {"id": 777}, "text": "Explain omen"}},
        )
        assert response.status_code == 200
    finally:
        app.dependency_overrides.pop(get_vocabulary_agent_runner, None)


def test_webhook_rejects_wrong_secret_when_configured(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(get_settings(), "telegram_webhook_secret", "expected-secret")

    response = client.post(
        "/api/v1/telegram/webhook",
        json={"message": {"chat": {"id": 555}, "text": "hello"}},
        headers={"X-Telegram-Bot-Api-Secret-Token": "wrong-secret"},
    )

    assert response.status_code == 401

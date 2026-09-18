from fastapi.testclient import TestClient

from app.agents.vocabulary_agent import VocabularyAgentRunner
from app.api.routes.chat import get_vocabulary_agent_runner
from app.main import app
from app.schemas.chat import AgentAction, ChatResponse
from app.services.groq_service import GroqVocabularyService


class SuccessfulAgentRunner:
    def run(self, message, request_id, tools, collection_id=None):
        assert message == "Explain omen"
        assert collection_id == "collection-a"
        assert tools.user_id == "user-a"
        return ChatResponse(
            message="An omen is a sign of what may happen.",
            actions=[
                AgentAction(
                    type="vocabulary_save",
                    status="success",
                    message="Saved omen.",
                )
            ],
            request_id=request_id,
        )


def test_chat_route_uses_authenticated_user_context(client: TestClient, monkeypatch) -> None:
    app.dependency_overrides[get_vocabulary_agent_runner] = lambda: SuccessfulAgentRunner()
    monkeypatch.setattr(
        "app.api.routes.chat.GroqVocabularyService",
        lambda **kwargs: GroqVocabularyService("", "test", client=object()),
    )

    response = client.post(
        "/api/v1/chat",
        json={"message": "Explain omen", "collection_id": "collection-a"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "An omen is a sign of what may happen."
    assert response.json()["actions"][0]["status"] == "success"
    assert response.json()["request_id"]


def test_chat_route_requires_a_nonempty_message(client: TestClient) -> None:
    response = client.post("/api/v1/chat", json={"message": ""})

    assert response.status_code == 422


def test_chat_route_reports_missing_groq_configuration(client: TestClient) -> None:
    app.dependency_overrides[get_vocabulary_agent_runner] = lambda: VocabularyAgentRunner(
        api_key="",
        model="test-model",
    )
    response = client.post("/api/v1/chat", json={"message": "Explain omen"})

    assert response.status_code == 503
    assert response.json()["detail"]["error_code"] == "GROQ_NOT_CONFIGURED"
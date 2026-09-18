from fastapi.testclient import TestClient

from app.api.routes.vocabulary import get_groq_vocabulary_service
from app.main import app
from app.schemas.vocabulary import VocabularyExplanation
from app.services.groq_service import GroqServiceError


class SuccessfulGroqService:
    def explain_term(self, term, sentence_context=None, difficulty_level="simple"):
        assert sentence_context == "He saw it as an omen."
        assert difficulty_level == "simple"
        return VocabularyExplanation(
            term=term,
            normalized_term="omen",
            part_of_speech="noun",
            meaning="A sign that something may happen.",
            simple_meaning="A sign about the future.",
            contextual_meaning="Here it suggests guidance about what comes next.",
            example="They considered the rainbow a good omen.",
            synonyms=["sign", "portent"],
            usage_note=None,
            confidence=0.96,
        )


class FailingGroqService:
    def explain_term(self, term, sentence_context=None, difficulty_level="simple"):
        raise GroqServiceError("GROQ_TIMEOUT", "The explanation request timed out.", 504)


def test_explain_route_returns_validated_explanation(client: TestClient) -> None:
    app.dependency_overrides[get_groq_vocabulary_service] = lambda: SuccessfulGroqService()

    response = client.post(
        "/api/v1/vocabulary/explain",
        json={
            "term": "omen",
            "sentence_context": "He saw it as an omen.",
            "difficulty_level": "simple",
        },
    )

    assert response.status_code == 200
    assert response.json()["simple_meaning"] == "A sign about the future."
    assert response.json()["confidence"] == 0.96


def test_explain_route_preserves_provider_failure(client: TestClient) -> None:
    app.dependency_overrides[get_groq_vocabulary_service] = lambda: FailingGroqService()

    response = client.post("/api/v1/vocabulary/explain", json={"term": "omen"})

    assert response.status_code == 504
    assert response.json()["detail"]["error_code"] == "GROQ_TIMEOUT"
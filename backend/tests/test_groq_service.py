import json
from types import SimpleNamespace

import pytest

from app.services.groq_service import GroqServiceError, GroqVocabularyService


class FakeCompletions:
    def __init__(self, content: str):
        self.content = content
        self.arguments = None

    def create(self, **kwargs):
        self.arguments = kwargs
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self.content))]
        )


class FakeGroqClient:
    def __init__(self, content: str):
        self.chat = SimpleNamespace(completions=FakeCompletions(content))


def test_explain_term_requests_json_and_validates_the_response():
    content = json.dumps(
        {
            "term": "stolen into",
            "normalized_term": "steal into",
            "part_of_speech": "verb phrase",
            "pronunciation": "/stiːl ˈɪntuː/",
            "meaning": "Entered quietly or secretly.",
            "simple_meaning": "Went in quietly without being noticed.",
            "contextual_meaning": "Here, stolen describes quiet movement, not theft.",
            "example": "He stole into the room without a sound.",
            "synonyms": ["slipped into", "sneaked into"],
            "usage_note": "This is a literary use of steal.",
            "confidence": 0.94,
        }
    )
    client = FakeGroqClient(content)
    service = GroqVocabularyService("", "test-model", client=client)

    result = service.explain_term(
        "stolen into",
        sentence_context="He had stolen into the room.",
        difficulty_level="simple",
    )

    arguments = client.chat.completions.arguments
    assert arguments["response_format"] == {"type": "json_object"}
    assert "He had stolen into the room." in arguments["messages"][1]["content"]
    assert result.normalized_term == "steal into"
    assert result.pronunciation == "/stiːl ˈɪntuː/"
    assert result.confidence == 0.94


def test_explain_term_rejects_unstructured_model_output():
    service = GroqVocabularyService("", "test-model", client=FakeGroqClient("Not JSON"))

    with pytest.raises(GroqServiceError) as error:
        service.explain_term("omen")

    assert error.value.error_code == "GROQ_INVALID_RESPONSE"
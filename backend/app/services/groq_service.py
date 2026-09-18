import ssl
from typing import Any, Optional

import httpx
import truststore
from groq import APIConnectionError, APIStatusError, APITimeoutError, Groq
from pydantic import ValidationError

from app.schemas.vocabulary import VocabularyExplanation


class GroqServiceError(Exception):
    def __init__(self, error_code: str, message: str, status_code: int = 502):
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.status_code = status_code


class GroqVocabularyService:
    def __init__(
        self,
        api_key: str,
        model: str,
        temperature: float = 0.3,
        client: Any | None = None,
    ):
        if not api_key and client is None:
            raise GroqServiceError(
                "GROQ_NOT_CONFIGURED",
                "Groq is not configured.",
                503,
            )
        self.model = model
        self.temperature = temperature
        self.client = client or Groq(
            api_key=api_key,
            timeout=15.0,
            max_retries=2,
            http_client=httpx.Client(
                verify=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT),
            ),
        )

    def explain_term(
        self,
        term: str,
        sentence_context: Optional[str] = None,
        difficulty_level: str = "simple",
    ) -> VocabularyExplanation:
        context = sentence_context or "No sentence context was provided."
        user_prompt = (
            f"Term or phrase: {term}\n"
            f"Sentence context: {context}\n"
            f"Explanation level: {difficulty_level}"
        )

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                max_tokens=900,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You explain English words and phrases for readers. Return one JSON object "
                            "with exactly these keys: term, normalized_term, part_of_speech, pronunciation, meaning, "
                            "simple_meaning, contextual_meaning, example, synonyms, usage_note, confidence. "
                            "Use null when context, part of speech, pronunciation, or a usage note is not applicable. "
                            "synonyms must be an array of strings and confidence must be between 0 and 1."
                        ),
                    },
                    {"role": "user", "content": user_prompt},
                ],
            )
        except APITimeoutError as exc:
            raise GroqServiceError("GROQ_TIMEOUT", "The explanation request timed out.", 504) from exc
        except APIConnectionError as exc:
            raise GroqServiceError("GROQ_UNAVAILABLE", "Groq could not be reached.", 503) from exc
        except APIStatusError as exc:
            status_code = 429 if exc.status_code == 429 else 502
            error_code = "GROQ_RATE_LIMITED" if exc.status_code == 429 else "GROQ_REQUEST_FAILED"
            raise GroqServiceError(error_code, "Groq could not generate an explanation.", status_code) from exc

        if not completion.choices or not completion.choices[0].message.content:
            raise GroqServiceError("GROQ_EMPTY_RESPONSE", "Groq returned an empty explanation.")

        try:
            explanation = VocabularyExplanation.model_validate_json(
                completion.choices[0].message.content
            )
        except ValidationError as exc:
            raise GroqServiceError(
                "GROQ_INVALID_RESPONSE",
                "Groq returned an invalid explanation.",
            ) from exc

        return explanation.model_copy(update={"term": term})
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.agents.vocabulary_agent import VocabularyAgentError, VocabularyAgentRunner
from app.api.deps import get_current_user_id
from app.config.settings import get_settings
from app.db.session import get_session
from app.schemas.chat import ChatRequest, ChatResponse
from app.security.notion_tokens import NotionTokenEncryptionError, NotionTokenVault
from app.services.groq_service import GroqServiceError, GroqVocabularyService
from app.services.notion_service import NotionService
from app.tools.vocabulary_agent_tools import VocabularyAgentTools

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


def get_vocabulary_agent_runner() -> VocabularyAgentRunner:
    settings = get_settings()
    return VocabularyAgentRunner(
        api_key=settings.groq_api_key,
        model=settings.groq_agent_model,
        temperature=settings.groq_temperature,
    )


@router.post("", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
    runner: VocabularyAgentRunner = Depends(get_vocabulary_agent_runner),
):
    settings = get_settings()
    try:
        vault = (
            NotionTokenVault(settings.notion_token_encryption_key)
            if settings.notion_token_encryption_key
            else None
        )
        tools = VocabularyAgentTools(
            session=session,
            user_id=user_id,
            groq=GroqVocabularyService(
                api_key=settings.groq_api_key,
                model=settings.groq_model,
                temperature=settings.groq_temperature,
            ),
            notion=NotionService(
                base_url=settings.notion_api_base_url,
                api_version=settings.notion_api_version,
            ),
            token_vault=vault,
        )
        return runner.run(
            message=payload.message,
            collection_id=payload.collection_id,
            request_id=str(uuid.uuid4()),
            tools=tools,
        )
    except (VocabularyAgentError, GroqServiceError, NotionTokenEncryptionError) as exc:
        if isinstance(exc, VocabularyAgentError):
            error_code = exc.error_code
            message = exc.message
            status_code = exc.status_code
        elif isinstance(exc, GroqServiceError):
            error_code = exc.error_code
            message = exc.message
            status_code = exc.status_code
        else:
            error_code = "NOTION_TOKEN_ENCRYPTION_NOT_CONFIGURED"
            message = "Notion token encryption is not configured."
            status_code = 503
        raise HTTPException(
            status_code=status_code,
            detail={"error_code": error_code, "message": message},
        ) from exc
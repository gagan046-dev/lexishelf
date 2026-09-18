import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlmodel import Session

from app.agents.vocabulary_agent import VocabularyAgentError, VocabularyAgentRunner
from app.api.deps import get_current_user_id
from app.api.routes.chat import get_vocabulary_agent_runner
from app.config.settings import get_settings
from app.db.session import get_session
from app.models.telegram_link import TelegramLinkCode
from app.repositories import telegram as telegram_repository
from app.schemas.telegram import TelegramLinkCodeResponse
from app.security.link_codes import generate_link_code, hash_link_code
from app.security.notion_tokens import NotionTokenEncryptionError, NotionTokenVault
from app.services.groq_service import GroqServiceError, GroqVocabularyService
from app.services.notion_service import NotionService
from app.services.telegram_service import TelegramService, TelegramServiceError
from app.tools.vocabulary_agent_tools import VocabularyAgentTools

router = APIRouter(prefix="/api/v1/telegram", tags=["telegram"])

LINK_CODE_EXPIRE_MINUTES = 10


@router.get("/link/code", response_model=TelegramLinkCodeResponse)
def get_link_code(
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
):
    telegram_repository.invalidate_codes_for_user(session, user_id)
    raw_code, code_hash = generate_link_code()
    expires_at = datetime.utcnow() + timedelta(minutes=LINK_CODE_EXPIRE_MINUTES)
    telegram_repository.add_link_code(
        session,
        TelegramLinkCode(user_id=user_id, code_hash=code_hash, expires_at=expires_at),
    )
    session.commit()
    return TelegramLinkCodeResponse(code=raw_code, expires_at=expires_at)


@router.post("/webhook", include_in_schema=False)
def telegram_webhook(
    payload: dict,
    session: Session = Depends(get_session),
    runner: VocabularyAgentRunner = Depends(get_vocabulary_agent_runner),
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    """Receives Telegram Bot API updates. Registered via Telegram's setWebhook, not called by clients."""
    settings = get_settings()
    if settings.telegram_webhook_secret and x_telegram_bot_api_secret_token != settings.telegram_webhook_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook secret")

    message = payload.get("message") or {}
    chat = message.get("chat") or {}
    chat_id = str(chat.get("id")) if chat.get("id") is not None else None
    text = (message.get("text") or "").strip()
    if not chat_id or not text:
        return {"ok": True}

    telegram = TelegramService(settings.telegram_bot_token)

    if text.startswith("/link"):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            _reply(telegram, chat_id, "Send /link followed by the 6-digit code shown in the LexiShelf app.")
            return {"ok": True}
        code_record = telegram_repository.get_valid_code_by_hash(session, hash_link_code(parts[1]))
        if not code_record:
            _reply(telegram, chat_id, "That code is invalid or expired. Generate a new one in the app.")
            return {"ok": True}
        telegram_repository.upsert_link(session, code_record.user_id, chat_id)
        code_record.used_at = datetime.utcnow()
        session.add(code_record)
        session.commit()
        _reply(telegram, chat_id, "Linked! You can now ask me to explain or save words right here.")
        return {"ok": True}

    link = telegram_repository.get_link_by_chat_id(session, chat_id)
    if not link:
        _reply(telegram, chat_id, "This chat isn't linked yet. Open LexiShelf, get a link code, then send /link CODE.")
        return {"ok": True}

    try:
        vault = (
            NotionTokenVault(settings.notion_token_encryption_key)
            if settings.notion_token_encryption_key
            else None
        )
        tools = VocabularyAgentTools(
            session=session,
            user_id=link.user_id,
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
        response = runner.run(
            message=text,
            collection_id=None,
            request_id=str(uuid.uuid4()),
            tools=tools,
        )
        _reply(telegram, chat_id, response.message)
    except (VocabularyAgentError, GroqServiceError) as exc:
        _reply(telegram, chat_id, f"I couldn't complete that: {exc.message}")
    except NotionTokenEncryptionError:
        _reply(telegram, chat_id, "Notion isn't configured on the server right now.")

    return {"ok": True}


def _reply(telegram: TelegramService, chat_id: str, text: str) -> None:
    try:
        telegram.send_message(chat_id, text)
    except TelegramServiceError:
        pass

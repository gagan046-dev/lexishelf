from datetime import datetime

from sqlmodel import Session, select

from app.models.telegram_link import TelegramLink, TelegramLinkCode


def add_link_code(session: Session, code: TelegramLinkCode) -> TelegramLinkCode:
    session.add(code)
    session.flush()
    session.refresh(code)
    return code


def get_valid_code_by_hash(session: Session, code_hash: str) -> TelegramLinkCode | None:
    record = session.exec(select(TelegramLinkCode).where(TelegramLinkCode.code_hash == code_hash)).first()
    if not record or record.used_at is not None:
        return None
    if record.expires_at < datetime.utcnow():
        return None
    return record


def invalidate_codes_for_user(session: Session, user_id: str) -> None:
    codes = session.exec(
        select(TelegramLinkCode).where(
            TelegramLinkCode.user_id == user_id,
            TelegramLinkCode.used_at.is_(None),
        )
    ).all()
    for code in codes:
        code.used_at = datetime.utcnow()
        session.add(code)


def get_link_by_chat_id(session: Session, chat_id: str) -> TelegramLink | None:
    return session.exec(select(TelegramLink).where(TelegramLink.chat_id == chat_id)).first()


def upsert_link(session: Session, user_id: str, chat_id: str) -> TelegramLink:
    existing = session.exec(select(TelegramLink).where(TelegramLink.user_id == user_id)).first()
    if existing:
        existing.chat_id = chat_id
        session.add(existing)
        return existing
    link = TelegramLink(user_id=user_id, chat_id=chat_id)
    session.add(link)
    session.flush()
    session.refresh(link)
    return link

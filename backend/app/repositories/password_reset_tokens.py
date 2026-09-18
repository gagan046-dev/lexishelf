from datetime import datetime

from sqlmodel import Session, select

from app.models.password_reset_token import PasswordResetToken


def add(session: Session, token: PasswordResetToken) -> PasswordResetToken:
    session.add(token)
    session.flush()
    session.refresh(token)
    return token


def get_valid_by_hash(session: Session, token_hash: str) -> PasswordResetToken | None:
    token = session.exec(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
    ).first()
    if not token or token.used_at is not None:
        return None
    if token.expires_at < datetime.utcnow():
        return None
    return token


def invalidate_all_for_user(session: Session, user_id: str) -> None:
    tokens = session.exec(
        select(PasswordResetToken).where(
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.used_at.is_(None),
        )
    ).all()
    for token in tokens:
        token.used_at = datetime.utcnow()
        session.add(token)

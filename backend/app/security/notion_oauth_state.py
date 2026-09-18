import secrets
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt


class NotionOAuthStateError(ValueError):
    pass


def create_notion_oauth_state(
    user_id: str,
    secret: str,
    algorithm: str,
    expires_minutes: int = 10,
) -> str:
    if not secret:
        raise NotionOAuthStateError("Notion OAuth state secret is not configured")
    return jwt.encode(
        {
            "sub": user_id,
            "purpose": "notion_oauth",
            "nonce": secrets.token_urlsafe(24),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=expires_minutes),
        },
        secret,
        algorithm=algorithm,
    )


def read_notion_oauth_state(state: str, secret: str, algorithm: str) -> str:
    try:
        payload = jwt.decode(state, secret, algorithms=[algorithm])
    except JWTError as exc:
        raise NotionOAuthStateError("Notion OAuth state is invalid or expired") from exc

    user_id = payload.get("sub")
    if payload.get("purpose") != "notion_oauth" or not user_id:
        raise NotionOAuthStateError("Notion OAuth state is invalid or expired")
    return user_id
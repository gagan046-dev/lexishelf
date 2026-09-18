import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class TelegramLink(SQLModel, table=True):
    """Maps a Telegram chat to the LexiShelf user who linked it. One chat per user."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(index=True, unique=True, foreign_key="user.id")
    chat_id: str = Field(index=True, unique=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TelegramLinkCode(SQLModel, table=True):
    """A short-lived, single-use code the user sends to the bot to link their chat."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(index=True, foreign_key="user.id")
    code_hash: str = Field(index=True, unique=True)
    expires_at: datetime
    used_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

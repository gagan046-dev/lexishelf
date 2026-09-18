import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


class NotionConnection(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(index=True, unique=True, foreign_key="user.id")
    access_token_encrypted: str
    refresh_token_encrypted: str | None = None
    bot_id: str | None = None
    workspace_id: str
    workspace_name: str
    workspace_icon: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

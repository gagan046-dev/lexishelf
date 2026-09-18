import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Collection(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(index=True, foreign_key="user.id")
    name: str
    description: Optional[str] = None
    notion_page_id: Optional[str] = None
    notion_page_url: Optional[str] = None
    theme_id: str = "midnight"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

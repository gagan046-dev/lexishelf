from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CollectionCreate(BaseModel):
    name: str
    description: Optional[str] = None
    notion_page_id: Optional[str] = None
    notion_page_url: Optional[str] = None
    theme_id: str = "midnight"


class CollectionRead(BaseModel):
    id: str
    name: str
    description: Optional[str]
    notion_page_id: Optional[str]
    notion_page_url: Optional[str]
    theme_id: str
    word_count: int = 0
    created_at: datetime
    updated_at: datetime


class CollectionDeleteRequest(BaseModel):
    """The client must explicitly confirm before a collection is deleted."""

    confirm: bool = False

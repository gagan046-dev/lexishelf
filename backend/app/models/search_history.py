import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class SearchHistory(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(index=True, foreign_key="user.id")
    query: str
    collection_id: Optional[str] = Field(default=None, foreign_key="collection.id")
    response_summary: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

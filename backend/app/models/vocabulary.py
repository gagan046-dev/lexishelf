import uuid
from datetime import datetime
from typing import List, Optional

from sqlmodel import JSON, Column, Field, SQLModel


class VocabularyEntry(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(index=True, foreign_key="user.id")
    collection_id: str = Field(index=True, foreign_key="collection.id")
    term: str
    phrase: Optional[str] = None
    sentence_context: Optional[str] = None
    meaning: Optional[str] = None
    simple_explanation: Optional[str] = None
    contextual_explanation: Optional[str] = None
    example: Optional[str] = None
    synonyms: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    part_of_speech: Optional[str] = None
    pronunciation: Optional[str] = None
    usage_note: Optional[str] = None
    difficulty_level: Optional[str] = None
    review_due_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    review_interval_days: float = 1.0
    review_ease: float = 2.5
    review_streak: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

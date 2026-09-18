from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class VocabularyExplainRequest(BaseModel):
    term: str = Field(min_length=1, max_length=300)
    sentence_context: Optional[str] = Field(default=None, max_length=4000)
    difficulty_level: Literal["simple", "standard", "advanced"] = "simple"


class VocabularyExplanation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    term: str = Field(min_length=1, max_length=300)
    normalized_term: str = Field(min_length=1, max_length=300)
    part_of_speech: Optional[str] = None
    pronunciation: Optional[str] = None
    meaning: str = Field(min_length=1)
    simple_meaning: str = Field(min_length=1)
    contextual_meaning: Optional[str] = None
    example: str = Field(min_length=1)
    synonyms: List[str] = Field(default_factory=list, max_length=12)
    usage_note: Optional[str] = None
    confidence: float = Field(ge=0, le=1)


class VocabularyEntryCreate(BaseModel):
    collection_id: str
    term: str
    phrase: Optional[str] = None
    sentence_context: Optional[str] = None
    meaning: Optional[str] = None
    simple_explanation: Optional[str] = None
    contextual_explanation: Optional[str] = None
    example: Optional[str] = None
    synonyms: List[str] = Field(default_factory=list)
    part_of_speech: Optional[str] = None
    pronunciation: Optional[str] = None
    usage_note: Optional[str] = None
    difficulty_level: Optional[Literal["simple", "standard", "advanced"]] = None


class VocabularyEntryRead(BaseModel):
    id: str
    collection_id: str
    term: str
    phrase: Optional[str]
    sentence_context: Optional[str]
    meaning: Optional[str]
    simple_explanation: Optional[str]
    contextual_explanation: Optional[str]
    example: Optional[str]
    synonyms: List[str]
    part_of_speech: Optional[str]
    pronunciation: Optional[str]
    usage_note: Optional[str]
    difficulty_level: Optional[str] = None
    notion_sync: Optional[Literal["synced", "not_linked", "failed"]] = None
    notion_message: Optional[str] = None
    review_due_at: datetime
    review_interval_days: float
    review_streak: int
    created_at: datetime
    updated_at: datetime


class VocabularyEntrySearchResult(VocabularyEntryRead):
    collection_name: str


class VocabularyReviewRequest(BaseModel):
    result: Literal["again", "hard", "good", "easy"]


class VocabularyReviewResult(BaseModel):
    entry_id: str
    review_due_at: datetime
    review_interval_days: float
    review_streak: int

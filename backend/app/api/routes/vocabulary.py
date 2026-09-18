from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.api.deps import get_current_user_id
from app.config.settings import get_settings
from app.db.session import get_session
from app.models.collection import Collection
from app.models.vocabulary import VocabularyEntry
from app.repositories import collections as collection_repository
from app.security.notion_tokens import NotionTokenEncryptionError, NotionTokenVault
from app.services.notion_service import NotionService
from app.services.spaced_repetition import schedule_next
from app.services.vocabulary_notion_sync import sync_vocabulary_to_notion
from app.repositories import vocabulary as vocabulary_repository
from app.schemas.common import ApiSuccess
from app.schemas.vocabulary import (
    VocabularyEntryCreate,
    VocabularyEntryRead,
    VocabularyEntrySearchResult,
    VocabularyExplainRequest,
    VocabularyExplanation,
    VocabularyReviewRequest,
    VocabularyReviewResult,
)
from app.services.groq_service import GroqServiceError, GroqVocabularyService

router = APIRouter(prefix="/api/v1/vocabulary", tags=["vocabulary"])


def get_groq_vocabulary_service() -> GroqVocabularyService:
    settings = get_settings()
    return GroqVocabularyService(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
        temperature=settings.groq_temperature,
    )


@router.post("/explain", response_model=VocabularyExplanation)
def explain_vocabulary(
    payload: VocabularyExplainRequest,
    user_id: str = Depends(get_current_user_id),
    groq_service: GroqVocabularyService = Depends(get_groq_vocabulary_service),
):
    del user_id
    try:
        return groq_service.explain_term(
            term=payload.term,
            sentence_context=payload.sentence_context,
            difficulty_level=payload.difficulty_level,
        )
    except GroqServiceError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"error_code": exc.error_code, "message": exc.message},
        ) from exc


@router.get("", response_model=List[VocabularyEntryRead])
def list_vocabulary(
    collection_id: str,
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
):
    _get_owned_collection(session, collection_id, user_id)
    return vocabulary_repository.list_owned_for_collection(session, collection_id, user_id)


@router.get("/search", response_model=List[VocabularyEntrySearchResult])
def search_vocabulary(
    query: str = Query(min_length=1, max_length=200),
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
):
    """Search saved words across every one of the user's collections."""
    results = vocabulary_repository.search_owned(session, user_id, query)
    return [
        VocabularyEntrySearchResult(
            **VocabularyEntryRead.model_validate(entry, from_attributes=True).model_dump(),
            collection_name=collection_name,
        )
        for entry, collection_name in results
    ]


@router.get("/review/due", response_model=List[VocabularyEntryRead])
def list_due_reviews(
    limit: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
):
    """Words due for spaced-repetition review right now, across every collection."""
    return vocabulary_repository.list_due_for_review(session, user_id, limit)


@router.post("", response_model=VocabularyEntryRead, status_code=status.HTTP_201_CREATED)
def create_vocabulary_entry(
    payload: VocabularyEntryCreate,
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
):
    collection = _get_owned_collection(session, payload.collection_id, user_id)
    entry = VocabularyEntry(user_id=user_id, **payload.model_dump())
    vocabulary_repository.add(session, entry)
    session.commit()
    settings = get_settings()
    try:
        token_vault = (
            NotionTokenVault(settings.notion_token_encryption_key)
            if settings.notion_token_encryption_key
            else None
        )
    except NotionTokenEncryptionError:
        token_vault = None
    sync = sync_vocabulary_to_notion(
        session=session,
        user_id=user_id,
        collection=collection,
        entry=entry,
        notion=NotionService(
            base_url=settings.notion_api_base_url,
            api_version=settings.notion_api_version,
        ),
        token_vault=token_vault,
    )
    return VocabularyEntryRead.model_validate(entry, from_attributes=True).model_copy(
        update={"notion_sync": sync.status, "notion_message": sync.message},
    )


@router.delete("/{entry_id}", response_model=ApiSuccess)
def delete_vocabulary_entry(
    entry_id: str,
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
):
    entry = vocabulary_repository.get_owned(session, entry_id, user_id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vocabulary entry not found")

    vocabulary_repository.delete(session, entry)
    session.commit()

    return ApiSuccess(data={"deleted_entry_id": entry_id})


@router.post("/{entry_id}/review", response_model=VocabularyReviewResult)
def review_vocabulary_entry(
    entry_id: str,
    payload: VocabularyReviewRequest,
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
):
    """Grade a spaced-repetition review and reschedule the entry's next due date."""
    entry = vocabulary_repository.get_owned(session, entry_id, user_id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vocabulary entry not found")

    from datetime import datetime, timedelta

    new_interval, new_ease, new_streak = schedule_next(
        entry.review_interval_days, entry.review_ease, entry.review_streak, payload.result
    )
    entry.review_interval_days = new_interval
    entry.review_ease = new_ease
    entry.review_streak = new_streak
    entry.review_due_at = datetime.utcnow() + timedelta(days=new_interval)
    session.add(entry)
    session.commit()

    return VocabularyReviewResult(
        entry_id=entry.id,
        review_due_at=entry.review_due_at,
        review_interval_days=entry.review_interval_days,
        review_streak=entry.review_streak,
    )


def _get_owned_collection(session: Session, collection_id: str, user_id: str) -> Collection:
    collection = collection_repository.get_owned(session, collection_id, user_id)
    if not collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    return collection

from sqlmodel import Session, func, select

from app.models.collection import Collection
from app.models.vocabulary import VocabularyEntry


def list_owned_for_collection(
    session: Session,
    collection_id: str,
    user_id: str,
) -> list[VocabularyEntry]:
    return list(
        session.exec(
            select(VocabularyEntry).where(
                VocabularyEntry.collection_id == collection_id,
                VocabularyEntry.user_id == user_id,
            )
        ).all()
    )


def search_owned(session: Session, user_id: str, query: str, limit: int = 50) -> list[tuple[VocabularyEntry, str]]:
    """Search a user's saved words across every collection by term."""
    like_query = f"%{query.strip().lower()}%"
    statement = (
        select(VocabularyEntry, Collection.name)
        .join(Collection, Collection.id == VocabularyEntry.collection_id)
        .where(
            VocabularyEntry.user_id == user_id,
            func.lower(VocabularyEntry.term).like(like_query),
        )
        .order_by(VocabularyEntry.created_at.desc())
        .limit(limit)
    )
    return [(entry, name) for entry, name in session.exec(statement).all()]


def list_due_for_review(session: Session, user_id: str, limit: int = 20) -> list[VocabularyEntry]:
    from datetime import datetime

    statement = (
        select(VocabularyEntry)
        .where(
            VocabularyEntry.user_id == user_id,
            VocabularyEntry.review_due_at <= datetime.utcnow(),
        )
        .order_by(VocabularyEntry.review_due_at.asc())
        .limit(limit)
    )
    return list(session.exec(statement).all())


def get_owned(session: Session, entry_id: str, user_id: str) -> VocabularyEntry | None:
    return session.exec(
        select(VocabularyEntry).where(
            VocabularyEntry.id == entry_id,
            VocabularyEntry.user_id == user_id,
        )
    ).first()


def add(session: Session, entry: VocabularyEntry) -> VocabularyEntry:
    session.add(entry)
    session.flush()
    session.refresh(entry)
    return entry


def delete(session: Session, entry: VocabularyEntry) -> None:
    session.delete(entry)


def delete_owned_for_collection(session: Session, collection_id: str, user_id: str) -> None:
    for entry in list_owned_for_collection(session, collection_id, user_id):
        session.delete(entry)
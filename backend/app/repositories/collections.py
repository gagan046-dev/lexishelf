from sqlmodel import Session, select

from app.models.collection import Collection


def list_owned(session: Session, user_id: str) -> list[Collection]:
    return list(session.exec(select(Collection).where(Collection.user_id == user_id)).all())


def get_owned(session: Session, collection_id: str, user_id: str) -> Collection | None:
    return session.exec(
        select(Collection).where(
            Collection.id == collection_id,
            Collection.user_id == user_id,
        )
    ).first()


def add(session: Session, collection: Collection) -> Collection:
    session.add(collection)
    session.flush()
    session.refresh(collection)
    return collection


def delete(session: Session, collection: Collection) -> None:
    session.delete(collection)
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.api.deps import get_current_user_id
from app.config.settings import get_settings
from app.db.session import get_session
from app.models.collection import Collection
from app.repositories import collections as collection_repository
from app.repositories import notion_connections as connection_repository
from app.repositories import vocabulary as vocabulary_repository
from app.schemas.collection import CollectionCreate, CollectionDeleteRequest, CollectionRead
from app.schemas.common import ApiSuccess
from app.security.notion_tokens import NotionTokenEncryptionError, NotionTokenVault
from app.services.notion_service import NotionService, NotionServiceError

router = APIRouter(prefix="/api/v1/collections", tags=["collections"])


def get_collection_notion_service() -> NotionService:
    settings = get_settings()
    return NotionService(
        base_url=settings.notion_api_base_url,
        api_version=settings.notion_api_version,
    )


def _to_read_model(collection: Collection, word_count: int) -> CollectionRead:
    return CollectionRead(
        id=collection.id,
        name=collection.name,
        description=collection.description,
        notion_page_id=collection.notion_page_id,
        notion_page_url=collection.notion_page_url,
        theme_id=collection.theme_id,
        word_count=word_count,
        created_at=collection.created_at,
        updated_at=collection.updated_at,
    )


@router.get("", response_model=List[CollectionRead])
def list_collections(
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
):
    collections = collection_repository.list_owned(session, user_id)
    results = []
    for collection in collections:
        word_count = len(vocabulary_repository.list_owned_for_collection(session, collection.id, user_id))
        results.append(_to_read_model(collection, word_count))
    return results


@router.post("", response_model=CollectionRead, status_code=status.HTTP_201_CREATED)
def create_collection(
    payload: CollectionCreate,
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
    notion: NotionService = Depends(get_collection_notion_service),
):
    values = payload.model_dump()
    if payload.notion_page_id:
        connection = connection_repository.get_owned(session, user_id)
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error_code": "NOTION_NOT_CONNECTED",
                    "message": "Connect Notion before linking a collection.",
                },
            )
        try:
            access_token = NotionTokenVault(
                get_settings().notion_token_encryption_key
            ).decrypt(connection.access_token_encrypted)
            page = notion.get_page(access_token, payload.notion_page_id)
        except NotionTokenEncryptionError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error_code": "NOTION_CONNECTION_INVALID",
                    "message": "The stored Notion connection could not be opened.",
                },
            ) from exc
        except NotionServiceError as exc:
            raise HTTPException(
                status_code=exc.status_code,
                detail={"error_code": exc.error_code, "message": exc.message},
            ) from exc
        values["notion_page_id"] = page.id
        values["notion_page_url"] = page.url

    collection = Collection(user_id=user_id, **values)
    collection_repository.add(session, collection)
    session.commit()
    return _to_read_model(collection, word_count=0)


@router.get("/{collection_id}", response_model=CollectionRead)
def get_collection(
    collection_id: str,
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
):
    collection = _get_owned_collection(session, collection_id, user_id)
    word_count = len(vocabulary_repository.list_owned_for_collection(session, collection.id, user_id))
    return _to_read_model(collection, word_count)


@router.delete("/{collection_id}", response_model=ApiSuccess)
def delete_collection(
    collection_id: str,
    payload: CollectionDeleteRequest,
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
):
    """Delete a collection and its vocabulary entries. Requires explicit confirmation."""
    if not payload.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "CONFIRMATION_REQUIRED",
                "message": "Set confirm=true to delete this collection.",
            },
        )

    collection = _get_owned_collection(session, collection_id, user_id)
    vocabulary_repository.delete_owned_for_collection(session, collection.id, user_id)
    # Flush the child deletes before the parent delete: without an ORM relationship() linking
    # the two tables, SQLAlchemy has no dependency info to order these correctly on commit, and
    # a database that enforces foreign keys (e.g. Postgres) will reject an out-of-order delete.
    session.flush()
    collection_repository.delete(session, collection)
    session.commit()

    return ApiSuccess(data={"deleted_collection_id": collection_id})


def _get_owned_collection(session: Session, collection_id: str, user_id: str) -> Collection:
    collection = collection_repository.get_owned(session, collection_id, user_id)
    if not collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    return collection

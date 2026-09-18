import json
from typing import Any

from sqlmodel import Session

from app.models.collection import Collection
from app.models.vocabulary import VocabularyEntry
from app.repositories import collections as collection_repository
from app.repositories import notion_connections as connection_repository
from app.repositories import vocabulary as vocabulary_repository
from app.schemas.chat import AgentAction
from app.security.notion_tokens import NotionTokenEncryptionError, NotionTokenVault
from app.services.groq_service import GroqServiceError, GroqVocabularyService
from app.services.notion_service import NotionService, NotionServiceError
from app.services.vocabulary_notion_sync import sync_vocabulary_to_notion


class VocabularyAgentTools:
    def __init__(
        self,
        session: Session,
        user_id: str,
        groq: GroqVocabularyService,
        notion: NotionService,
        token_vault: NotionTokenVault | None,
    ):
        self.session = session
        self.user_id = user_id
        self.groq = groq
        self.notion = notion
        self.token_vault = token_vault
        self.actions: list[AgentAction] = []

    def list_collections(self) -> str:
        """List the authenticated user's LexiShelf collections and linked Notion page IDs."""
        collections = collection_repository.list_owned(self.session, self.user_id)
        return self._success(
            {
                "collections": [
                    {
                        "id": collection.id,
                        "name": collection.name,
                        "notion_page_id": collection.notion_page_id,
                    }
                    for collection in collections
                ]
            }
        )

    def get_collection(self, collection_id: str) -> str:
        """Get one collection owned by the authenticated user using its exact ID."""
        collection = collection_repository.get_owned(self.session, collection_id, self.user_id)
        if not collection:
            return self._failure("COLLECTION_NOT_FOUND", "Collection not found.")
        return self._success(
            {
                "id": collection.id,
                "name": collection.name,
                "notion_page_id": collection.notion_page_id,
            }
        )

    def explain_term(
        self,
        term: str,
        sentence_context: str = "",
        difficulty_level: str = "simple",
    ) -> str:
        """Explain a word or phrase, optionally using its sentence context."""
        try:
            explanation = self.groq.explain_term(
                term=term,
                sentence_context=sentence_context or None,
                difficulty_level=difficulty_level,
            )
        except GroqServiceError as exc:
            return self._failure(exc.error_code, exc.message)
        return self._success(explanation.model_dump())

    def save_vocabulary(
        self,
        collection_id: str,
        term: str,
        example: str = "",
        synonyms: list[str] | None = None,
        part_of_speech: str = "",
        pronunciation: str = "",
        sentence_context: str = "",
        usage_note: str = "",
        meaning: str = "",
        simple_explanation: str = "",
        contextual_explanation: str = "",
        difficulty_level: str = "",
    ) -> str:
        """Save a vocabulary entry, including its explanation text when the user wants it kept."""
        collection = collection_repository.get_owned(self.session, collection_id, self.user_id)
        if not collection:
            return self._record_failure(
                "vocabulary_save",
                "COLLECTION_NOT_FOUND",
                "The vocabulary entry was not saved because the collection was not found.",
            )

        entry = VocabularyEntry(
            user_id=self.user_id,
            collection_id=collection.id,
            term=term,
            sentence_context=sentence_context or None,
            example=example or None,
            synonyms=synonyms or [],
            part_of_speech=part_of_speech or None,
            pronunciation=pronunciation or None,
            usage_note=usage_note or None,
            meaning=meaning or None,
            simple_explanation=simple_explanation or None,
            contextual_explanation=contextual_explanation or None,
            difficulty_level=difficulty_level or None,
        )
        vocabulary_repository.add(self.session, entry)
        self.session.commit()
        sync = sync_vocabulary_to_notion(
            session=self.session,
            user_id=self.user_id,
            collection=collection,
            entry=entry,
            notion=self.notion,
            token_vault=self.token_vault,
        )
        return self._record_success(
            "vocabulary_save",
            sync.message,
            {
                "entry_id": entry.id,
                "collection_id": collection.id,
                "notion_sync": sync.status,
            },
        )

    def search_notion_pages(self, query: str = "") -> str:
        """Search pages shared with the authenticated user's connected Notion workspace."""
        access_token = self._notion_access_token()
        if isinstance(access_token, str) and access_token.startswith("{"):
            return access_token
        try:
            result = self.notion.search_pages(access_token, query=query)
        except NotionServiceError as exc:
            return self._failure(exc.error_code, exc.message)
        return self._success(result.model_dump())

    def append_to_collection_notion(self, collection_id: str, content: str) -> str:
        """Append Markdown to the Notion page linked to an owned LexiShelf collection."""
        collection = collection_repository.get_owned(self.session, collection_id, self.user_id)
        if not collection:
            return self._record_failure(
                "notion_append",
                "COLLECTION_NOT_FOUND",
                "Notion was not updated because the collection was not found.",
            )
        if not collection.notion_page_id:
            return self._record_failure(
                "notion_append",
                "NOTION_PAGE_NOT_LINKED",
                f'{collection.name} is not linked to a Notion page.',
            )

        access_token = self._notion_access_token()
        if isinstance(access_token, str) and access_token.startswith("{"):
            error = json.loads(access_token)
            return self._record_failure(
                "notion_append",
                error["error_code"],
                error["message"],
            )
        try:
            result = self.notion.append_content(access_token, collection.notion_page_id, content)
        except NotionServiceError as exc:
            return self._record_failure("notion_append", exc.error_code, exc.message)
        return self._record_success(
            "notion_append",
            f"Appended content to the Notion page linked to {collection.name}.",
            result.model_dump(),
        )

    def create_notion_page(self, parent_page_id: str, title: str, content: str = "") -> str:
        """Create a page under an authorized Notion parent page."""
        access_token = self._notion_access_token()
        if isinstance(access_token, str) and access_token.startswith("{"):
            error = json.loads(access_token)
            return self._record_failure(
                "notion_create_page",
                error["error_code"],
                error["message"],
            )
        try:
            result = self.notion.create_page(
                access_token,
                parent_page_id,
                title,
                content or None,
            )
        except NotionServiceError as exc:
            return self._record_failure("notion_create_page", exc.error_code, exc.message)
        return self._record_success(
            "notion_create_page",
            f'Created Notion page "{title}".',
            result.model_dump(),
        )

    def link_collection_to_notion(self, collection_id: str, notion_page_id: str) -> str:
        """Link an owned LexiShelf collection to a verified, authorized Notion page."""
        collection = collection_repository.get_owned(self.session, collection_id, self.user_id)
        if not collection:
            return self._record_failure(
                "notion_link",
                "COLLECTION_NOT_FOUND",
                "The collection was not linked because it could not be found.",
            )

        access_token = self._notion_access_token()
        if isinstance(access_token, str) and access_token.startswith("{"):
            error = json.loads(access_token)
            return self._record_failure("notion_link", error["error_code"], error["message"])
        try:
            page = self.notion.get_page(access_token, notion_page_id)
        except NotionServiceError as exc:
            return self._record_failure("notion_link", exc.error_code, exc.message)

        collection.notion_page_id = page.id
        collection.notion_page_url = page.url
        self.session.add(collection)
        self.session.commit()
        return self._record_success(
            "notion_link",
            f'Linked {collection.name} to the Notion page "{page.title}".',
            {
                "collection_id": collection.id,
                "notion_page_id": page.id,
                "notion_page_url": page.url,
            },
        )

    def create_collection(self, name: str, description: str = "") -> str:
        """Create a non-destructive LexiShelf collection for the authenticated user."""
        collection = Collection(
            user_id=self.user_id,
            name=name,
            description=description or None,
        )
        collection_repository.add(self.session, collection)
        self.session.commit()
        return self._record_success(
            "collection_create",
            f'Created collection "{name}".',
            {"collection_id": collection.id},
        )

    def _notion_access_token(self) -> str:
        connection = connection_repository.get_owned(self.session, self.user_id)
        if not connection:
            return self._failure(
                "NOTION_NOT_CONNECTED",
                "Connect a Notion workspace before using Notion actions.",
            )
        if not self.token_vault:
            return self._failure(
                "NOTION_TOKEN_ENCRYPTION_NOT_CONFIGURED",
                "Notion token encryption is not configured.",
            )
        try:
            return self.token_vault.decrypt(connection.access_token_encrypted)
        except NotionTokenEncryptionError:
            return self._failure(
                "NOTION_CONNECTION_INVALID",
                "The stored Notion connection could not be opened.",
            )

    @staticmethod
    def _success(data: dict[str, Any]) -> str:
        return json.dumps({"success": True, "data": data}, default=str)

    @staticmethod
    def _failure(error_code: str, message: str) -> str:
        return json.dumps({"success": False, "error_code": error_code, "message": message})

    def _record_success(self, action_type: str, message: str, data: dict[str, Any]) -> str:
        self.actions.append(
            AgentAction(type=action_type, status="success", message=message, data=data)
        )
        return self._success(data)

    def _record_failure(self, action_type: str, error_code: str, message: str) -> str:
        self.actions.append(
            AgentAction(
                type=action_type,
                status="failure",
                error_code=error_code,
                message=message,
            )
        )
        return self._failure(error_code, message)
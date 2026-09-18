from dataclasses import dataclass

from sqlmodel import Session

from app.models.collection import Collection
from app.models.vocabulary import VocabularyEntry
from app.repositories import notion_connections as connection_repository
from app.security.notion_tokens import NotionTokenEncryptionError, NotionTokenVault
from app.services.notion_service import NotionService, NotionServiceError


@dataclass(frozen=True)
class NotionSyncResult:
    status: str
    message: str


def sync_vocabulary_to_notion(
    session: Session,
    user_id: str,
    collection: Collection,
    entry: VocabularyEntry,
    notion: NotionService,
    token_vault: NotionTokenVault | None,
) -> NotionSyncResult:
    if not collection.notion_page_id:
        return NotionSyncResult("not_linked", "Saved locally. This collection is not linked to Notion.")

    connection = connection_repository.get_owned(session, user_id)
    if not connection or not token_vault:
        return NotionSyncResult("failed", "Saved locally, but the Notion connection is unavailable.")

    try:
        access_token = token_vault.decrypt(connection.access_token_encrypted)
        notion.append_content(access_token, collection.notion_page_id, format_vocabulary_markdown(entry))
    except NotionTokenEncryptionError:
        return NotionSyncResult("failed", "Saved locally, but the Notion connection could not be opened.")
    except NotionServiceError as exc:
        return NotionSyncResult("failed", f"Saved locally, but Notion was not updated: {exc.message}")

    return NotionSyncResult("synced", "Saved to this collection and its linked Notion page.")


def format_vocabulary_markdown(entry: VocabularyEntry) -> str:
    lines = [f"## {entry.term}", ""]
    fields = (
        ("Meaning", entry.meaning),
        ("Simple meaning", entry.simple_explanation),
        ("Contextual meaning", entry.contextual_explanation),
        ("Type", entry.part_of_speech),
        ("Pronunciation", entry.pronunciation),
        ("Source sentence", entry.sentence_context),
        ("Example", entry.example),
        ("Synonyms", ", ".join(entry.synonyms) if entry.synonyms else None),
        ("Usage", entry.usage_note),
    )
    lines.extend(f"**{label}:** {value}" for label, value in fields if value)
    lines.extend(["", "---"])
    return "\n".join(lines)
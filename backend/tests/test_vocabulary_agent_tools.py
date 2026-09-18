import json

import pytest

from app.models.collection import Collection
from app.models.notion_connection import NotionConnection
from app.models.user import User
from app.models.vocabulary import VocabularyEntry
from app.schemas.notion import NotionPageSummary, NotionWriteResult
from app.security.notion_tokens import NotionTokenVault
from app.services.groq_service import GroqVocabularyService
from app.services.notion_service import NotionService
from app.tools.vocabulary_agent_tools import VocabularyAgentTools


@pytest.fixture(autouse=True)
def _seed_users(session):
    # Foreign keys are enforced now, so collections/connections need real owning users.
    session.add(User(id="user-a", email="user-a@test.local", hashed_password="unused"))
    session.add(User(id="user-b", email="user-b@test.local", hashed_password="unused"))
    session.commit()


def make_tools(session, user_id="user-a"):
    return VocabularyAgentTools(
        session=session,
        user_id=user_id,
        groq=GroqVocabularyService("", "test", client=object()),
        notion=NotionService(),
        token_vault=None,
    )


def test_save_vocabulary_is_scoped_to_authenticated_user(session):
    collection = Collection(user_id="user-b", name="Private")
    session.add(collection)
    session.commit()
    tools = make_tools(session)

    result = json.loads(
        tools.save_vocabulary(
            collection_id=collection.id,
            term="omen",
            part_of_speech="noun",
        )
    )

    assert result["success"] is False
    assert result["error_code"] == "COLLECTION_NOT_FOUND"
    assert tools.actions[0].status == "failure"


def test_save_vocabulary_records_success_only_after_persistence(session):
    collection = Collection(user_id="user-a", name="The Alchemist")
    session.add(collection)
    session.commit()
    tools = make_tools(session)

    result = json.loads(
        tools.save_vocabulary(
            collection_id=collection.id,
            term="omen",
            part_of_speech="noun",
            example="They saw it as an omen.",
            synonyms=["sign"],
        )
    )

    assert result["success"] is True
    assert tools.actions[0].status == "success"
    assert tools.actions[0].data["entry_id"]
    saved = session.get(VocabularyEntry, tools.actions[0].data["entry_id"])
    assert saved is not None
    assert saved.part_of_speech == "noun"
    assert saved.example == "They saw it as an omen."
    assert saved.meaning is None


def test_save_vocabulary_appends_metadata_without_meanings_to_linked_notion(session):
    vault = NotionTokenVault(FERNET_KEY)
    collection = Collection(user_id="user-a", name="The Alchemist", notion_page_id="page-a")
    session.add(collection)
    session.add(
        NotionConnection(
            user_id="user-a",
            access_token_encrypted=vault.encrypt("notion-token"),
            workspace_id="workspace-a",
            workspace_name="Reading",
        )
    )
    session.commit()
    notion = FakeNotionService()
    tools = VocabularyAgentTools(
        session=session,
        user_id="user-a",
        groq=GroqVocabularyService("", "test", client=object()),
        notion=notion,
        token_vault=vault,
    )

    result = json.loads(
        tools.save_vocabulary(
            collection_id=collection.id,
            term="omen",
            part_of_speech="noun",
            example="They saw it as an omen.",
            usage_note="Often used for a sign of a future event.",
        )
    )

    assert result["success"] is True
    assert result["data"]["notion_sync"] == "synced"
    assert notion.append_arguments is not None
    assert "**Type:** noun" in notion.append_arguments[2]
    assert "**Example:** They saw it as an omen." in notion.append_arguments[2]
    assert "Meaning" not in notion.append_arguments[2]


def test_create_notion_page_records_confirmed_provider_result(session):
    vault = NotionTokenVault(FERNET_KEY)
    session.add(
        NotionConnection(
            user_id="user-a",
            access_token_encrypted=vault.encrypt("notion-token"),
            workspace_id="workspace-a",
            workspace_name="Reading",
        )
    )
    session.commit()
    notion = FakeNotionService()
    tools = VocabularyAgentTools(
        session=session,
        user_id="user-a",
        groq=GroqVocabularyService("", "test", client=object()),
        notion=notion,
        token_vault=vault,
    )

    result = json.loads(tools.create_notion_page("parent-a", "Reading Notes", "Intro"))

    assert result["success"] is True
    assert notion.arguments == ("notion-token", "parent-a", "Reading Notes", "Intro")
    assert tools.actions[0].type == "notion_create_page"
    assert tools.actions[0].status == "success"


def test_link_collection_to_notion_verifies_page_and_persists_link(session):
    collection = Collection(user_id="user-a", name="The Alchemist")
    vault = NotionTokenVault(FERNET_KEY)
    session.add(collection)
    session.add(
        NotionConnection(
            user_id="user-a",
            access_token_encrypted=vault.encrypt("notion-token"),
            workspace_id="workspace-a",
            workspace_name="Reading",
        )
    )
    session.commit()
    notion = FakeNotionService()
    tools = VocabularyAgentTools(
        session=session,
        user_id="user-a",
        groq=GroqVocabularyService("", "test", client=object()),
        notion=notion,
        token_vault=vault,
    )

    result = json.loads(tools.link_collection_to_notion(collection.id, "page-a"))

    assert result["success"] is True
    assert collection.notion_page_id == "page-a"
    assert collection.notion_page_url == "https://notion.so/page-a"
    assert tools.actions[0].type == "notion_link"


FERNET_KEY = "MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA="


class FakeNotionService:
    def __init__(self):
        self.arguments = None
        self.append_arguments = None

    def create_page(self, access_token, parent_page_id, title, content=None):
        self.arguments = (access_token, parent_page_id, title, content)
        return NotionWriteResult(page_id="page-a", page_url="https://notion.so/page-a")

    def get_page(self, access_token, page_id):
        assert access_token == "notion-token"
        return NotionPageSummary(id=page_id, title="The Alchemist", url="https://notion.so/page-a")

    def append_content(self, access_token, page_id, content):
        self.append_arguments = (access_token, page_id, content)
        return NotionWriteResult(page_id=page_id)
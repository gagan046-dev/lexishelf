import json

import httpx
import pytest

from app.services.notion_service import NotionService, NotionServiceError


def test_search_pages_sends_required_headers_and_maps_page_titles():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer secret-token"
        assert request.headers["Notion-Version"] == "2026-03-11"
        assert json.loads(request.content) == {
            "query": "Alchemist",
            "filter": {"property": "object", "value": "page"},
            "page_size": 20,
        }
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "object": "page",
                        "id": "page-1",
                        "url": "https://notion.so/page-1",
                        "properties": {
                            "title": {
                                "type": "title",
                                "title": [{"plain_text": "The Alchemist"}],
                            }
                        },
                    }
                ],
                "has_more": True,
                "next_cursor": "opaque-cursor",
            },
        )

    service = NotionService(transport=httpx.MockTransport(handler))

    result = service.search_pages("secret-token", query="Alchemist")

    assert result.pages[0].title == "The Alchemist"
    assert result.next_cursor == "opaque-cursor"


def test_create_and_append_only_succeed_after_notion_confirms():
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/v1/pages":
            return httpx.Response(200, json={"id": "new-page", "url": "https://notion.so/new-page"})
        return httpx.Response(200, json={"object": "page_markdown", "id": "new-page", "markdown": "word"})

    service = NotionService(transport=httpx.MockTransport(handler))

    created = service.create_page("token", "parent", "Words", "# Words")
    appended = service.append_content("token", "new-page", "## Serendipity")

    create_payload = json.loads(requests[0].content)
    append_payload = json.loads(requests[1].content)
    assert created.page_id == "new-page"
    assert appended.page_id == "new-page"
    assert create_payload["markdown"] == "# Words"
    assert append_payload["insert_content"]["position"] == {"type": "end"}


def test_notion_unauthorized_is_a_structured_failure():
    service = NotionService(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(401, json={"code": "unauthorized"})
        )
    )

    with pytest.raises(NotionServiceError) as error:
        service.get_page("expired-token", "page-1")

    assert error.value.error_code == "NOTION_UNAUTHORIZED"
    assert error.value.status_code == 401
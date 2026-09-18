import ssl
from typing import Any, Optional

import httpx
import truststore

from app.schemas.notion import NotionPageSearchResult, NotionPageSummary, NotionWriteResult


class NotionServiceError(Exception):
    def __init__(self, error_code: str, message: str, status_code: int = 502):
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.status_code = status_code


class NotionService:
    def __init__(
        self,
        base_url: str = "https://api.notion.com",
        api_version: str = "2026-03-11",
        timeout_seconds: float = 10.0,
        transport: httpx.BaseTransport | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_version = api_version
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    def search_pages(
        self,
        access_token: str,
        query: str = "",
        start_cursor: Optional[str] = None,
        page_size: int = 20,
    ) -> NotionPageSearchResult:
        payload: dict[str, Any] = {
            "query": query,
            "filter": {"property": "object", "value": "page"},
            "page_size": page_size,
        }
        if start_cursor:
            payload["start_cursor"] = start_cursor

        data = self._request("POST", "/v1/search", access_token, json=payload)
        pages = [self._page_summary(item) for item in data.get("results", []) if item.get("object") == "page"]
        return NotionPageSearchResult(
            pages=pages,
            has_more=bool(data.get("has_more", False)),
            next_cursor=data.get("next_cursor"),
        )

    def get_page(self, access_token: str, page_id: str) -> NotionPageSummary:
        data = self._request("GET", f"/v1/pages/{page_id}", access_token)
        return self._page_summary(data)

    def create_page(
        self,
        access_token: str,
        parent_page_id: str,
        title: str,
        content: Optional[str] = None,
    ) -> NotionWriteResult:
        payload: dict[str, Any] = {
            "parent": {"type": "page_id", "page_id": parent_page_id},
            "properties": {
                "title": {
                    "type": "title",
                    "title": [{"type": "text", "text": {"content": title}}],
                }
            },
        }
        if content:
            payload["markdown"] = content

        data = self._request("POST", "/v1/pages", access_token, json=payload)
        return NotionWriteResult(page_id=data["id"], page_url=data.get("url"))

    def append_content(self, access_token: str, page_id: str, content: str) -> NotionWriteResult:
        payload = {
            "type": "insert_content",
            "insert_content": {
                "content": content,
                "position": {"type": "end"},
            },
        }
        data = self._request("PATCH", f"/v1/pages/{page_id}/markdown", access_token, json=payload)
        return NotionWriteResult(page_id=data["id"])

    def _request(
        self,
        method: str,
        path: str,
        access_token: str,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Notion-Version": self.api_version,
            "Content-Type": "application/json",
        }
        try:
            with httpx.Client(
                base_url=self.base_url,
                headers=headers,
                timeout=self.timeout_seconds,
                transport=self.transport,
                verify=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT),
            ) as client:
                response = client.request(method, path, json=json)
        except httpx.HTTPError as exc:
            raise NotionServiceError(
                "NOTION_UNAVAILABLE",
                "Notion could not be reached. Try again shortly.",
            ) from exc

        if not response.is_success:
            self._raise_for_response(response)

        try:
            return response.json()
        except ValueError as exc:
            raise NotionServiceError(
                "NOTION_INVALID_RESPONSE",
                "Notion returned an invalid response.",
            ) from exc

    @staticmethod
    def _page_summary(page: dict[str, Any]) -> NotionPageSummary:
        title = "Untitled"
        for value in page.get("properties", {}).values():
            if value.get("type") != "title":
                continue
            plain_text = "".join(item.get("plain_text", "") for item in value.get("title", []))
            if plain_text:
                title = plain_text
            break
        return NotionPageSummary(id=page["id"], title=title, url=page.get("url"))

    @staticmethod
    def _raise_for_response(response: httpx.Response) -> None:
        errors = {
            400: ("NOTION_INVALID_REQUEST", "Notion rejected the request."),
            401: ("NOTION_UNAUTHORIZED", "Notion authorization has expired."),
            403: ("NOTION_FORBIDDEN", "The Notion connection lacks permission for this action."),
            404: ("NOTION_NOT_FOUND", "The Notion page was not found or is not shared with the connection."),
            409: ("NOTION_CONFLICT", "Notion could not complete the request because of a conflict."),
            429: ("NOTION_RATE_LIMITED", "Notion is rate limiting requests. Try again shortly."),
        }
        if response.status_code >= 500:
            error_code, message = "NOTION_UNAVAILABLE", "Notion is temporarily unavailable."
        else:
            error_code, message = errors.get(
                response.status_code,
                ("NOTION_ERROR", "Notion could not complete the request."),
            )
        raise NotionServiceError(error_code, message, response.status_code)
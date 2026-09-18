from typing import Optional

import httpx
from pydantic import BaseModel, ValidationError

from app.services.notion_service import NotionServiceError


class NotionOAuthCredentials(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    bot_id: Optional[str] = None
    workspace_id: str
    workspace_name: Optional[str] = None
    workspace_icon: Optional[str] = None


class NotionOAuthService:
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

    def exchange_code(
        self,
        client_id: str,
        client_secret: str,
        code: str,
        redirect_uri: str,
    ) -> NotionOAuthCredentials:
        try:
            with httpx.Client(
                base_url=self.base_url,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Notion-Version": self.api_version,
                },
                auth=httpx.BasicAuth(client_id, client_secret),
                timeout=self.timeout_seconds,
                transport=self.transport,
            ) as client:
                response = client.post(
                    "/v1/oauth/token",
                    json={
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": redirect_uri,
                    },
                )
        except httpx.HTTPError as exc:
            raise NotionServiceError(
                "NOTION_OAUTH_UNAVAILABLE",
                "Notion authorization could not be reached.",
            ) from exc

        if not response.is_success:
            error_code = "NOTION_OAUTH_INVALID_GRANT" if response.status_code == 400 else "NOTION_OAUTH_FAILED"
            raise NotionServiceError(
                error_code,
                "Notion authorization could not be completed.",
                response.status_code,
            )

        try:
            return NotionOAuthCredentials.model_validate(response.json())
        except (ValueError, ValidationError) as exc:
            raise NotionServiceError(
                "NOTION_INVALID_RESPONSE",
                "Notion returned an invalid authorization response.",
            ) from exc
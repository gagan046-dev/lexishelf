from typing import Optional

from pydantic import BaseModel, Field


class NotionPageSummary(BaseModel):
    id: str
    title: str
    url: Optional[str] = None


class NotionPageSearchResult(BaseModel):
    pages: list[NotionPageSummary]
    has_more: bool = False
    next_cursor: Optional[str] = None


class NotionAuthorizationUrl(BaseModel):
    authorization_url: str


class NotionConnectionRead(BaseModel):
    connected: bool = True
    workspace_id: str
    workspace_name: str
    workspace_icon: Optional[str] = None


class NotionCreatePageRequest(BaseModel):
    parent_page_id: str
    title: str = Field(min_length=1, max_length=2000)
    content: Optional[str] = None


class NotionAppendContentRequest(BaseModel):
    content: str = Field(min_length=1)


class NotionWriteResult(BaseModel):
    page_id: str
    page_url: Optional[str] = None
from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    collection_id: str | None = None
    conversation_id: str | None = Field(default=None, max_length=200)


class AgentAction(BaseModel):
    type: str
    status: Literal["success", "failure"]
    message: str
    error_code: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    message: str
    actions: list[AgentAction] = Field(default_factory=list)
    request_id: str
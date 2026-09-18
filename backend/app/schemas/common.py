from typing import Any, Optional

from pydantic import BaseModel


class ApiError(BaseModel):
    success: bool = False
    error_code: str
    message: str


class ApiSuccess(BaseModel):
    success: bool = True
    data: Optional[Any] = None

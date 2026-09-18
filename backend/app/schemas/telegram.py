from datetime import datetime

from pydantic import BaseModel


class TelegramLinkCodeResponse(BaseModel):
    code: str
    expires_at: datetime

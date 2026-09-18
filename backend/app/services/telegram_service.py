import ssl

import httpx
import truststore


class TelegramServiceError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class TelegramService:
    def __init__(self, bot_token: str, timeout_seconds: float = 10.0):
        self.bot_token = bot_token
        self.timeout_seconds = timeout_seconds

    def send_message(self, chat_id: str, text: str) -> None:
        if not self.bot_token:
            raise TelegramServiceError("Telegram is not configured.")
        try:
            with httpx.Client(
                base_url=f"https://api.telegram.org/bot{self.bot_token}",
                timeout=self.timeout_seconds,
                verify=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT),
            ) as client:
                response = client.post("/sendMessage", json={"chat_id": chat_id, "text": text})
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise TelegramServiceError("Could not reach Telegram.") from exc

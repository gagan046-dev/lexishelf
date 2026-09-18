from cryptography.fernet import Fernet, InvalidToken


class NotionTokenEncryptionError(ValueError):
    pass


class NotionTokenVault:
    def __init__(self, encryption_key: str):
        if not encryption_key:
            raise NotionTokenEncryptionError("NOTION_TOKEN_ENCRYPTION_KEY is not configured")

        try:
            self._fernet = Fernet(encryption_key.encode("ascii"))
        except (ValueError, UnicodeEncodeError) as exc:
            raise NotionTokenEncryptionError("NOTION_TOKEN_ENCRYPTION_KEY is invalid") from exc

    def encrypt(self, access_token: str) -> str:
        if not access_token:
            raise NotionTokenEncryptionError("Notion access token cannot be empty")
        return self._fernet.encrypt(access_token.encode("utf-8")).decode("ascii")

    def decrypt(self, encrypted_token: str) -> str:
        try:
            return self._fernet.decrypt(encrypted_token.encode("ascii")).decode("utf-8")
        except (InvalidToken, UnicodeDecodeError, UnicodeEncodeError) as exc:
            raise NotionTokenEncryptionError("Stored Notion access token cannot be decrypted") from exc
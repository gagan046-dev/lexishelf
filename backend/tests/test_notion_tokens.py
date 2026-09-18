import pytest
from cryptography.fernet import Fernet

from app.security.notion_tokens import NotionTokenEncryptionError, NotionTokenVault


def test_notion_token_vault_encrypts_and_decrypts_without_plaintext_storage():
    vault = NotionTokenVault(Fernet.generate_key().decode("ascii"))
    access_token = "secret_notion_token"

    encrypted_token = vault.encrypt(access_token)

    assert encrypted_token != access_token
    assert access_token not in encrypted_token
    assert vault.decrypt(encrypted_token) == access_token


def test_notion_token_vault_rejects_missing_key():
    with pytest.raises(NotionTokenEncryptionError, match="not configured"):
        NotionTokenVault("")
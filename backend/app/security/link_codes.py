import hashlib
import secrets


def generate_link_code() -> tuple[str, str]:
    """Return (raw_code, code_hash). A short numeric code that's easy to type in a chat app."""
    raw_code = f"{secrets.randbelow(1_000_000):06d}"
    return raw_code, hash_link_code(raw_code)


def hash_link_code(raw_code: str) -> str:
    return hashlib.sha256(raw_code.strip().encode("utf-8")).hexdigest()

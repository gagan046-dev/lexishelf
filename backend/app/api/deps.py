from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt

from app.config.settings import get_settings

settings = get_settings()


def get_current_user_id(authorization: str = Header(default=None)) -> str:
    """Resolve the trusted, authenticated user id from the request's JWT.

    The mobile app and the LLM/agent must never be able to supply user_id directly;
    it is always derived here, server-side, from a verified token.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = jwt.decode(token, settings.jwt_signing_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing subject")

    return user_id

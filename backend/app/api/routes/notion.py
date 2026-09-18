import json
from html import escape
from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from sqlmodel import Session

from app.api.deps import get_current_user_id
from app.config.settings import get_settings
from app.db.session import get_session
from app.repositories import notion_connections as connection_repository
from app.schemas.common import ApiSuccess
from app.schemas.notion import (
    NotionAppendContentRequest,
    NotionAuthorizationUrl,
    NotionConnectionRead,
    NotionCreatePageRequest,
    NotionPageSearchResult,
    NotionPageSummary,
)
from app.security.notion_oauth_state import (
    NotionOAuthStateError,
    create_notion_oauth_state,
    read_notion_oauth_state,
)
from app.security.notion_tokens import NotionTokenEncryptionError, NotionTokenVault
from app.services.notion_oauth import NotionOAuthService
from app.services.notion_service import NotionService, NotionServiceError

router = APIRouter(prefix="/api/v1/notion", tags=["notion"])


def get_notion_service() -> NotionService:
    settings = get_settings()
    return NotionService(
        base_url=settings.notion_api_base_url,
        api_version=settings.notion_api_version,
    )


def get_notion_oauth_service() -> NotionOAuthService:
    settings = get_settings()
    return NotionOAuthService(
        base_url=settings.notion_api_base_url,
        api_version=settings.notion_api_version,
    )


@router.get("/oauth/authorize", response_model=NotionAuthorizationUrl)
def authorize_notion(
    user_id: str = Depends(get_current_user_id),
):
    settings = get_settings()
    if not settings.notion_client_id or not settings.notion_redirect_uri:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error_code": "NOTION_OAUTH_NOT_CONFIGURED",
                "message": "Notion OAuth is not configured.",
            },
        )

    state_secret = settings.notion_oauth_state_secret or settings.jwt_signing_secret
    try:
        state_token = create_notion_oauth_state(
            user_id,
            state_secret,
            settings.jwt_algorithm,
        )
    except NotionOAuthStateError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error_code": "NOTION_OAUTH_NOT_CONFIGURED",
                "message": "Notion OAuth state signing is not configured.",
            },
        ) from exc

    query = urlencode(
        {
            "client_id": settings.notion_client_id,
            "redirect_uri": settings.notion_redirect_uri,
            "response_type": "code",
            "owner": "user",
            "state": state_token,
        }
    )
    return NotionAuthorizationUrl(
        authorization_url=f"{settings.notion_api_base_url.rstrip('/')}/v1/oauth/authorize?{query}"
    )


@router.get("/oauth/callback", response_class=HTMLResponse)
def notion_oauth_callback(
    code: Optional[str] = None,
    state_token: Optional[str] = Query(default=None, alias="state"),
    error: Optional[str] = None,
    session: Session = Depends(get_session),
    oauth: NotionOAuthService = Depends(get_notion_oauth_service),
):
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "NOTION_OAUTH_DENIED", "message": "Notion access was not granted."},
        )
    if not code or not state_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "NOTION_OAUTH_INVALID_CALLBACK", "message": "Missing OAuth callback data."},
        )

    settings = get_settings()
    state_secret = settings.notion_oauth_state_secret or settings.jwt_signing_secret
    try:
        user_id = read_notion_oauth_state(state_token, state_secret, settings.jwt_algorithm)
    except NotionOAuthStateError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "NOTION_OAUTH_INVALID_STATE", "message": str(exc)},
        ) from exc

    credentials = _call_notion(
        oauth.exchange_code,
        settings.notion_client_id,
        settings.notion_client_secret,
        code,
        settings.notion_redirect_uri,
    )
    try:
        vault = NotionTokenVault(settings.notion_token_encryption_key)
        access_token_encrypted = vault.encrypt(credentials.access_token)
        refresh_token_encrypted = (
            vault.encrypt(credentials.refresh_token) if credentials.refresh_token else None
        )
    except NotionTokenEncryptionError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error_code": "NOTION_TOKEN_ENCRYPTION_NOT_CONFIGURED",
                "message": "Notion token encryption is not configured.",
            },
        ) from exc

    connection = connection_repository.upsert(
        session,
        user_id=user_id,
        access_token_encrypted=access_token_encrypted,
        refresh_token_encrypted=refresh_token_encrypted,
        workspace_id=credentials.workspace_id,
        workspace_name=credentials.workspace_name or "Notion workspace",
        bot_id=credentials.bot_id,
        workspace_icon=credentials.workspace_icon,
    )
    session.commit()
    app_url = json.dumps(settings.app_web_url.rstrip("/"))
    workspace_name = escape(connection.workspace_name)
    return HTMLResponse(
        content=f"""<!doctype html>
<html lang="en">
    <head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Notion connected</title></head>
    <body style="margin:0;background:#0b0f1a;color:#f4f6fb;font-family:system-ui,sans-serif;display:grid;min-height:100vh;place-items:center">
        <main style="max-width:420px;padding:32px;text-align:center">
            <h1 style="font-size:24px;margin:0 0 10px">Notion connected</h1>
            <p style="color:#aab2c8;line-height:1.5">{workspace_name} is ready. Returning to your collection draft...</p>
            <a id="return-link" style="color:#8ca8ff" href="#">Return to LexiShelf</a>
        </main>
        <script>
            const appUrl = {app_url};
            document.getElementById("return-link").href = appUrl;
            if (window.opener && !window.opener.closed) {{
                window.opener.postMessage({{ type: "lexishelf:notion-connected" }}, "*");
                window.close();
            }} else {{
                window.location.replace(appUrl);
            }}
        </script>
    </body>
</html>"""
    )


@router.get("/connection", response_model=NotionConnectionRead)
def get_connection(
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
):
    connection = connection_repository.get_owned(session, user_id)
    if not connection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notion connection not found")
    return _connection_read(connection)


@router.get("/pages/search", response_model=NotionPageSearchResult)
def search_pages(
    query: str = "",
    start_cursor: Optional[str] = None,
    page_size: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
    notion: NotionService = Depends(get_notion_service),
):
    access_token = _get_access_token(session, user_id)
    return _call_notion(
        notion.search_pages,
        access_token,
        query=query,
        start_cursor=start_cursor,
        page_size=page_size,
    )


@router.get("/pages/{page_id}", response_model=NotionPageSummary)
def get_page(
    page_id: str,
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
    notion: NotionService = Depends(get_notion_service),
):
    return _call_notion(notion.get_page, _get_access_token(session, user_id), page_id)


@router.post("/pages", response_model=ApiSuccess, status_code=status.HTTP_201_CREATED)
def create_page(
    payload: NotionCreatePageRequest,
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
    notion: NotionService = Depends(get_notion_service),
):
    result = _call_notion(
        notion.create_page,
        _get_access_token(session, user_id),
        payload.parent_page_id,
        payload.title,
        payload.content,
    )
    return ApiSuccess(data=result.model_dump())


@router.post("/pages/{page_id}/append", response_model=ApiSuccess)
def append_content(
    page_id: str,
    payload: NotionAppendContentRequest,
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
    notion: NotionService = Depends(get_notion_service),
):
    result = _call_notion(
        notion.append_content,
        _get_access_token(session, user_id),
        page_id,
        payload.content,
    )
    return ApiSuccess(data=result.model_dump())


def _get_access_token(session: Session, user_id: str) -> str:
    connection = connection_repository.get_owned(session, user_id)
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error_code": "NOTION_NOT_CONNECTED",
                "message": "Connect a Notion workspace before using Notion actions.",
            },
        )

    try:
        vault = NotionTokenVault(get_settings().notion_token_encryption_key)
        return vault.decrypt(connection.access_token_encrypted)
    except NotionTokenEncryptionError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "NOTION_CONNECTION_INVALID",
                "message": "The stored Notion connection could not be opened.",
            },
        ) from exc


def _call_notion(operation, *args, **kwargs):
    try:
        return operation(*args, **kwargs)
    except NotionServiceError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"error_code": exc.error_code, "message": exc.message},
        ) from exc


def _connection_read(connection) -> NotionConnectionRead:
    return NotionConnectionRead(
        workspace_id=connection.workspace_id,
        workspace_name=connection.workspace_name,
        workspace_icon=connection.workspace_icon,
    )
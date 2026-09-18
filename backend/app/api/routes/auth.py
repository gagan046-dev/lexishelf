from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session

from app.config.settings import get_settings
from app.db.session import get_session
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User
from app.repositories import password_reset_tokens as reset_token_repository
from app.repositories import users as user_repository
from app.schemas.auth import (
    AuthCredentials,
    AuthUser,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    TokenResponse,
)
from app.security.auth import (
    create_access_token,
    generate_reset_token,
    hash_password,
    hash_reset_token,
    verify_password,
)
from app.security.rate_limit import auth_rate_limiter

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

RESET_TOKEN_EXPIRE_MINUTES = 30
GENERIC_FORGOT_PASSWORD_MESSAGE = "If an account uses this email, a reset code has been sent."


def _enforce_rate_limit(request: Request, max_hits: int, window_seconds: float) -> None:
    client_host = request.client.host if request.client else "unknown"
    key = f"{client_host}:{request.url.path}"
    if not auth_rate_limiter.allow(key, max_hits, window_seconds):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"error_code": "RATE_LIMITED", "message": "Too many attempts. Try again shortly."},
        )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: AuthCredentials, request: Request, session: Session = Depends(get_session)):
    _enforce_rate_limit(request, max_hits=10, window_seconds=300)
    if user_repository.get_by_email(session, payload.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error_code": "EMAIL_IN_USE", "message": "An account already uses this email."},
        )

    user = User(email=payload.email, hashed_password=hash_password(payload.password))
    user_repository.add(session, user)
    session.commit()
    return _token_response(user)


@router.post("/login", response_model=TokenResponse)
def login(payload: AuthCredentials, request: Request, session: Session = Depends(get_session)):
    _enforce_rate_limit(request, max_hits=10, window_seconds=300)
    user = user_repository.get_by_email(session, payload.email)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "INVALID_CREDENTIALS", "message": "Email or password is incorrect."},
        )
    return _token_response(user)


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(payload: ForgotPasswordRequest, request: Request, session: Session = Depends(get_session)):
    """Always returns a generic message so requests cannot reveal whether an email is registered."""
    _enforce_rate_limit(request, max_hits=5, window_seconds=900)
    user = user_repository.get_by_email(session, payload.email)
    dev_reset_token: str | None = None

    if user:
        reset_token_repository.invalidate_all_for_user(session, user.id)
        raw_token, token_hash = generate_reset_token()
        reset_token_repository.add(
            session,
            PasswordResetToken(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=datetime.utcnow() + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES),
            ),
        )
        session.commit()
        if get_settings().environment != "production":
            dev_reset_token = raw_token

    return ForgotPasswordResponse(message=GENERIC_FORGOT_PASSWORD_MESSAGE, dev_reset_token=dev_reset_token)


@router.post("/reset-password", response_model=TokenResponse)
def reset_password(payload: ResetPasswordRequest, request: Request, session: Session = Depends(get_session)):
    _enforce_rate_limit(request, max_hits=10, window_seconds=300)
    token = reset_token_repository.get_valid_by_hash(session, hash_reset_token(payload.token))
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "INVALID_RESET_TOKEN", "message": "This reset code is invalid or has expired."},
        )

    user = user_repository.get_by_id(session, token.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "INVALID_RESET_TOKEN", "message": "This reset code is invalid or has expired."},
        )

    user.hashed_password = hash_password(payload.new_password)
    session.add(user)
    reset_token_repository.invalidate_all_for_user(session, user.id)
    session.commit()
    return _token_response(user)


def _token_response(user: User) -> TokenResponse:
    settings = get_settings()
    token = create_access_token(
        user.id,
        settings.jwt_signing_secret,
        settings.jwt_algorithm,
        settings.jwt_expire_minutes,
    )
    return TokenResponse(
        access_token=token,
        user=AuthUser(id=user.id, email=user.email),
    )
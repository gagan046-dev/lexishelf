from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.api.deps import get_current_user_id
from app.db.session import get_session
from app.main import app
from app.models import (  # noqa: F401
    collection,
    notion_connection,
    password_reset_token,
    search_history,
    telegram_link,
    user,
    vocabulary,
)
from app.models.user import User
from app.security.rate_limit import auth_rate_limiter


@pytest.fixture(autouse=True)
def _reset_auth_rate_limiter():
    auth_rate_limiter.reset()
    yield


@pytest.fixture
def session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    SQLModel.metadata.create_all(engine)
    with Session(engine) as database_session:
        yield database_session
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def current_user() -> dict[str, str]:
    return {"id": "user-a"}


@pytest.fixture
def client(
    session: Session,
    current_user: dict[str, str],
) -> Generator[TestClient, None, None]:
    def override_session() -> Generator[Session, None, None]:
        yield session

    def override_user_id() -> str:
        user_id = current_user["id"]
        # Foreign keys are enforced now (matching production Postgres), so any user_id the
        # fake-auth override hands out needs a real backing row, created on first use.
        if not session.get(User, user_id):
            session.add(User(id=user_id, email=f"{user_id}@test.local", hashed_password="unused"))
            session.commit()
        return user_id

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_current_user_id] = override_user_id
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
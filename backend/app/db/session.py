from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine

from app.config.settings import get_settings

settings = get_settings()

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, echo=False, connect_args=connect_args)

if settings.database_url.startswith("sqlite"):
    # SQLite ignores foreign key constraints unless explicitly enabled per connection; without
    # this, integrity bugs (e.g. deleting a parent row before its children) stay silent locally
    # and only surface against a database that enforces them, like Postgres in production.
    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def init_db() -> None:
    # Import models so SQLModel metadata knows about every table before create_all.
    from app.models import (  # noqa: F401
        collection,
        notion_connection,
        password_reset_token,
        search_history,
        telegram_link,
        user,
        vocabulary,
    )

    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session

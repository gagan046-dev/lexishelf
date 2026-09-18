from datetime import datetime

from sqlmodel import Session, select

from app.models.notion_connection import NotionConnection


def get_owned(session: Session, user_id: str) -> NotionConnection | None:
    return session.exec(
        select(NotionConnection).where(NotionConnection.user_id == user_id)
    ).first()


def add(session: Session, connection: NotionConnection) -> NotionConnection:
    session.add(connection)
    session.flush()
    session.refresh(connection)
    return connection


def upsert(
    session: Session,
    user_id: str,
    access_token_encrypted: str,
    refresh_token_encrypted: str | None,
    workspace_id: str,
    workspace_name: str,
    bot_id: str | None = None,
    workspace_icon: str | None = None,
) -> NotionConnection:
    connection = get_owned(session, user_id)
    if connection is None:
        connection = NotionConnection(
            user_id=user_id,
            access_token_encrypted=access_token_encrypted,
            refresh_token_encrypted=refresh_token_encrypted,
            workspace_id=workspace_id,
            workspace_name=workspace_name,
            bot_id=bot_id,
            workspace_icon=workspace_icon,
        )
    else:
        connection.access_token_encrypted = access_token_encrypted
        connection.refresh_token_encrypted = refresh_token_encrypted
        connection.workspace_id = workspace_id
        connection.workspace_name = workspace_name
        connection.bot_id = bot_id
        connection.workspace_icon = workspace_icon
        connection.updated_at = datetime.utcnow()

    session.add(connection)
    session.flush()
    session.refresh(connection)
    return connection
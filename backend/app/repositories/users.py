from sqlmodel import Session, select

from app.models.user import User


def get_by_email(session: Session, email: str) -> User | None:
    return session.exec(select(User).where(User.email == email)).first()


def get_by_id(session: Session, user_id: str) -> User | None:
    return session.get(User, user_id)


def add(session: Session, user: User) -> User:
    session.add(user)
    session.flush()
    session.refresh(user)
    return user
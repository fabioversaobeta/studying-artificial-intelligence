import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


def get_by_id(db: Session, user_id: uuid.UUID) -> User | None:
    return db.get(User, user_id)


def get_by_email(db: Session, email: str) -> User | None:
    stmt = select(User).where(User.email == email.lower())
    return db.execute(stmt).scalar_one_or_none()


def create(db: Session, *, email: str, hashed_password: str, display_name: str) -> User:
    user = User(email=email.lower(), hashed_password=hashed_password, display_name=display_name)
    db.add(user)
    db.flush()
    return user

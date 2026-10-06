import uuid
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.revoked_token import RevokedToken


def is_revoked(db: Session, jti: uuid.UUID) -> bool:
    stmt = select(RevokedToken.id).where(RevokedToken.jti == jti)
    return db.execute(stmt).first() is not None


def revoke(
    db: Session, *, jti: uuid.UUID, user_id: uuid.UUID, token_type: str, expires_at: datetime
) -> bool:
    """Add `jti` to the denylist. Returns False if it was already there.

    Uses INSERT .. ON CONFLICT DO NOTHING on the unique `jti`, so two
    concurrent rotations of the same refresh token cannot both succeed.
    """
    stmt = (
        insert(RevokedToken)
        .values(
            id=uuid.uuid4(), jti=jti, user_id=user_id, token_type=token_type, expires_at=expires_at
        )
        .on_conflict_do_nothing(index_elements=["jti"])
        .returning(RevokedToken.id)
    )
    return db.execute(stmt).first() is not None


def delete_expired(db: Session, now: datetime) -> int:
    result = db.execute(delete(RevokedToken).where(RevokedToken.expires_at < now))
    return int(result.rowcount or 0)  # type: ignore[attr-defined]

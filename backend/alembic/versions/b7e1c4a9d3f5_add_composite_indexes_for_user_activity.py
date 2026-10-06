"""add composite per-user indexes for activity queries

Revision ID: b7e1c4a9d3f5
Revises: a3c5d7e9f1b2
Create Date: 2026-10-06 15:00:00.000000

Evidence (EXPLAIN ANALYZE on synthetic data, heavy user with ~30k rows) is in
docs/DECISIONS.md. Each composite index replaces the single-column user_id
index it extends (the leading column still serves plain per-user lookups and
the ON DELETE CASCADE from users).

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b7e1c4a9d3f5"
down_revision: Union[str, Sequence[str], None] = "a3c5d7e9f1b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(
        "ix_study_sessions_user_occurred_at",
        "study_sessions",
        ["user_id", sa.text("occurred_at DESC")],
    )
    op.create_index(
        "ix_study_sessions_user_competency", "study_sessions", ["user_id", "competency_id"]
    )
    op.drop_index(op.f("ix_study_sessions_user_id"), table_name="study_sessions")

    op.create_index("ix_xp_awards_user_created_at", "xp_awards", ["user_id", "created_at"])
    op.drop_index(op.f("ix_xp_awards_user_id"), table_name="xp_awards")

    op.create_index(
        "ix_challenge_submissions_user_challenge",
        "challenge_submissions",
        ["user_id", "challenge_id"],
    )
    op.create_index(
        "ix_challenge_submissions_user_submitted_at",
        "challenge_submissions",
        ["user_id", "submitted_at"],
    )
    op.drop_index(op.f("ix_challenge_submissions_user_id"), table_name="challenge_submissions")


def downgrade() -> None:
    """Downgrade schema."""
    op.create_index(
        op.f("ix_challenge_submissions_user_id"), "challenge_submissions", ["user_id"]
    )
    op.drop_index("ix_challenge_submissions_user_submitted_at", table_name="challenge_submissions")
    op.drop_index("ix_challenge_submissions_user_challenge", table_name="challenge_submissions")

    op.create_index(op.f("ix_xp_awards_user_id"), "xp_awards", ["user_id"])
    op.drop_index("ix_xp_awards_user_created_at", table_name="xp_awards")

    op.create_index(op.f("ix_study_sessions_user_id"), "study_sessions", ["user_id"])
    op.drop_index("ix_study_sessions_user_competency", table_name="study_sessions")
    op.drop_index("ix_study_sessions_user_occurred_at", table_name="study_sessions")

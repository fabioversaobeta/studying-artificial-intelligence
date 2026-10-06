"""add user preferred_language and the assessments / question bank

Revision ID: c9d2f6a1e4b7
Revises: b7e1c4a9d3f5
Create Date: 2026-10-06 18:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c9d2f6a1e4b7"
down_revision: Union[str, Sequence[str], None] = "b7e1c4a9d3f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column(
            "preferred_language",
            sa.Enum("EN", "PT_BR", name="language", native_enum=False, length=32),
            server_default="EN",
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "preferred_language")

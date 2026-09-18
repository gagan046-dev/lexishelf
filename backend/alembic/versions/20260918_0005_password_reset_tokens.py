"""Add password reset tokens."""

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260918_0005"
down_revision: str | None = "20260918_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "passwordresettoken",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_passwordresettoken_user_id", "passwordresettoken", ["user_id"], unique=False
    )
    op.create_index(
        "ix_passwordresettoken_token_hash", "passwordresettoken", ["token_hash"], unique=True
    )


def downgrade() -> None:
    op.drop_index("ix_passwordresettoken_token_hash", table_name="passwordresettoken")
    op.drop_index("ix_passwordresettoken_user_id", table_name="passwordresettoken")
    op.drop_table("passwordresettoken")

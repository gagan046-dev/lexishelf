"""Add spaced-repetition review scheduling to vocabulary entries."""

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260918_0006"
down_revision: str | None = "20260918_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("vocabularyentry") as batch_op:
        batch_op.add_column(
            sa.Column("review_due_at", sa.DateTime(), nullable=False, server_default=sa.func.now())
        )
        batch_op.add_column(
            sa.Column("review_interval_days", sa.Float(), nullable=False, server_default="1.0")
        )
        batch_op.add_column(
            sa.Column("review_ease", sa.Float(), nullable=False, server_default="2.5")
        )
        batch_op.add_column(
            sa.Column("review_streak", sa.Integer(), nullable=False, server_default="0")
        )
        batch_op.create_index(
            "ix_vocabularyentry_review_due_at", ["review_due_at"], unique=False
        )


def downgrade() -> None:
    with op.batch_alter_table("vocabularyentry") as batch_op:
        batch_op.drop_index("ix_vocabularyentry_review_due_at")
        batch_op.drop_column("review_streak")
        batch_op.drop_column("review_ease")
        batch_op.drop_column("review_interval_days")
        batch_op.drop_column("review_due_at")

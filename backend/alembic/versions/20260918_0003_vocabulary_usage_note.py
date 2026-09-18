"""Add vocabulary usage notes."""

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260918_0003"
down_revision: str | None = "20260917_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("vocabularyentry") as batch_op:
        batch_op.add_column(sa.Column("usage_note", sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("vocabularyentry") as batch_op:
        batch_op.drop_column("usage_note")
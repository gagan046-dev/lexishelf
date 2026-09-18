"""Add Telegram link and link-code tables."""

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260918_0007"
down_revision: str | None = "20260918_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "telegramlink",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("chat_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_telegramlink_user_id", "telegramlink", ["user_id"], unique=True)
    op.create_index("ix_telegramlink_chat_id", "telegramlink", ["chat_id"], unique=True)

    op.create_table(
        "telegramlinkcode",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("code_hash", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_telegramlinkcode_user_id", "telegramlinkcode", ["user_id"], unique=False)
    op.create_index("ix_telegramlinkcode_code_hash", "telegramlinkcode", ["code_hash"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_telegramlinkcode_code_hash", table_name="telegramlinkcode")
    op.drop_index("ix_telegramlinkcode_user_id", table_name="telegramlinkcode")
    op.drop_table("telegramlinkcode")

    op.drop_index("ix_telegramlink_chat_id", table_name="telegramlink")
    op.drop_index("ix_telegramlink_user_id", table_name="telegramlink")
    op.drop_table("telegramlink")

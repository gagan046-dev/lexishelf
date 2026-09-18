"""Store the complete encrypted Notion OAuth token pair."""

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260917_0002"
down_revision: str | None = "20260917_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("notionconnection") as batch_op:
        batch_op.add_column(sa.Column("refresh_token_encrypted", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("bot_id", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("workspace_icon", sa.String(), nullable=True))
        batch_op.drop_index("ix_notionconnection_user_id")
        batch_op.create_index("ix_notionconnection_user_id", ["user_id"], unique=True)


def downgrade() -> None:
    with op.batch_alter_table("notionconnection") as batch_op:
        batch_op.drop_index("ix_notionconnection_user_id")
        batch_op.create_index("ix_notionconnection_user_id", ["user_id"], unique=False)
        batch_op.drop_column("workspace_icon")
        batch_op.drop_column("bot_id")
        batch_op.drop_column("refresh_token_encrypted")
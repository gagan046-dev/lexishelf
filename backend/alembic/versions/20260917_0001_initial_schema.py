"""Create the initial LexiShelf schema."""

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260917_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_email", "user", ["email"], unique=True)

    op.create_table(
        "collection",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("notion_page_id", sa.String(), nullable=True),
        sa.Column("notion_page_url", sa.String(), nullable=True),
        sa.Column("theme_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_collection_user_id", "collection", ["user_id"], unique=False)

    op.create_table(
        "notionconnection",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("access_token_encrypted", sa.String(), nullable=False),
        sa.Column("workspace_id", sa.String(), nullable=False),
        sa.Column("workspace_name", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notionconnection_user_id", "notionconnection", ["user_id"], unique=False)

    op.create_table(
        "searchhistory",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("query", sa.String(), nullable=False),
        sa.Column("collection_id", sa.String(), nullable=True),
        sa.Column("response_summary", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["collection_id"], ["collection.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_searchhistory_user_id", "searchhistory", ["user_id"], unique=False)

    op.create_table(
        "vocabularyentry",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("collection_id", sa.String(), nullable=False),
        sa.Column("term", sa.String(), nullable=False),
        sa.Column("phrase", sa.String(), nullable=True),
        sa.Column("sentence_context", sa.String(), nullable=True),
        sa.Column("meaning", sa.String(), nullable=True),
        sa.Column("simple_explanation", sa.String(), nullable=True),
        sa.Column("contextual_explanation", sa.String(), nullable=True),
        sa.Column("example", sa.String(), nullable=True),
        sa.Column("synonyms", sa.JSON(), nullable=True),
        sa.Column("part_of_speech", sa.String(), nullable=True),
        sa.Column("pronunciation", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["collection_id"], ["collection.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_vocabularyentry_collection_id",
        "vocabularyentry",
        ["collection_id"],
        unique=False,
    )
    op.create_index("ix_vocabularyentry_user_id", "vocabularyentry", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_vocabularyentry_user_id", table_name="vocabularyentry")
    op.drop_index("ix_vocabularyentry_collection_id", table_name="vocabularyentry")
    op.drop_table("vocabularyentry")
    op.drop_index("ix_searchhistory_user_id", table_name="searchhistory")
    op.drop_table("searchhistory")
    op.drop_index("ix_notionconnection_user_id", table_name="notionconnection")
    op.drop_table("notionconnection")
    op.drop_index("ix_collection_user_id", table_name="collection")
    op.drop_table("collection")
    op.drop_index("ix_user_email", table_name="user")
    op.drop_table("user")
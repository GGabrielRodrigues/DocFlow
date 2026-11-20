"""Add media authorship and explicit sharing.

Revision ID: 0004_media_access
Revises: 0003_media_uploads, 0003_audit_log
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_media_access"
down_revision: str | Sequence[str] | None = ("0003_media_uploads", "0003_audit_log")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("media", sa.Column("author_id", sa.String(length=36), nullable=True))
    op.create_index("ix_media_author_id", "media", ["author_id"])
    op.create_foreign_key("fk_media_author_id", "media", "users", ["author_id"], ["id"])
    op.create_table(
        "media_shares",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("media_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(["media_id"], ["media.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("media_id", "user_id", name="uq_media_share"),
    )
    op.create_index("ix_media_shares_media_id", "media_shares", ["media_id"])
    op.create_index("ix_media_shares_user_id", "media_shares", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_media_shares_user_id", table_name="media_shares")
    op.drop_index("ix_media_shares_media_id", table_name="media_shares")
    op.drop_table("media_shares")
    op.drop_constraint("fk_media_author_id", "media", type_="foreignkey")
    op.drop_index("ix_media_author_id", table_name="media")
    op.drop_column("media", "author_id")

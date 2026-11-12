"""Add media upload records.

Revision ID: 0003_media_uploads
Revises: 0002_identity_registration
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003_media_uploads"
down_revision: Union[str, Sequence[str], None] = "0002_identity_registration"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "media",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.String(length=36), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("declared_duration_seconds", sa.Integer(), nullable=False),
        sa.Column("storage_bucket", sa.String(length=63), nullable=False),
        sa.Column("storage_key", sa.String(length=1024), nullable=False),
        sa.Column("multipart_upload_id", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_media_institution_id", "media", ["institution_id"])


def downgrade() -> None:
    op.drop_index("ix_media_institution_id", table_name="media")
    op.drop_table("media")

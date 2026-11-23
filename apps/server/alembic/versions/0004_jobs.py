"""Add asynchronous jobs table.

Revision ID: 0004_jobs
Revises: 0004_media_access
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_jobs"
down_revision: str | Sequence[str] | None = "0004_media_access"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.String(length=36), nullable=False),
        sa.Column("requested_by_id", sa.String(length=36), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("state", sa.String(length=20), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", sa.String(length=2000), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("resource_type", sa.String(length=50), nullable=False),
        sa.Column("resource_id", sa.String(length=36), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=True),
        sa.Column("celery_task_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"]),
        sa.ForeignKeyConstraint(["requested_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "institution_id",
            "idempotency_key",
            name="uq_jobs_institution_idempotency",
        ),
    )
    op.create_index("ix_jobs_institution_id", "jobs", ["institution_id"])
    op.create_index("ix_jobs_requested_by_id", "jobs", ["requested_by_id"])
    op.create_index("ix_jobs_type", "jobs", ["type"])
    op.create_index("ix_jobs_state", "jobs", ["state"])
    op.create_index("ix_jobs_resource_id", "jobs", ["resource_id"])
    if op.get_bind().dialect.name == "postgresql":
        op.execute("SELECT docflow_enable_tenant_rls('jobs')")


def downgrade() -> None:
    op.drop_index("ix_jobs_requested_by_id", table_name="jobs")
    op.drop_index("ix_jobs_resource_id", table_name="jobs")
    op.drop_index("ix_jobs_state", table_name="jobs")
    op.drop_index("ix_jobs_type", table_name="jobs")
    op.drop_index("ix_jobs_institution_id", table_name="jobs")
    op.drop_table("jobs")

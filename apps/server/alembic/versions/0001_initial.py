"""Create the institution root table.

Revision ID: 0001_initial
Revises:
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "institutions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    if op.get_bind().dialect.name == "postgresql":
        op.execute(
            """
        CREATE OR REPLACE FUNCTION docflow_enable_tenant_rls(target_table regclass)
        RETURNS void
        LANGUAGE plpgsql
        AS $$
        BEGIN
            EXECUTE format('ALTER TABLE %s ENABLE ROW LEVEL SECURITY', target_table);
            EXECUTE format('ALTER TABLE %s FORCE ROW LEVEL SECURITY', target_table);
            EXECUTE format(
                'CREATE POLICY tenant_isolation_policy ON %s '
                'USING (institution_id::text = current_setting(''app.current_institution_id'', true)) '
                'WITH CHECK (institution_id::text = current_setting(''app.current_institution_id'', true))',
                target_table
            );
        END;
        $$;
        """
        )


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP FUNCTION IF EXISTS docflow_enable_tenant_rls(regclass)")
    op.drop_table("institutions")

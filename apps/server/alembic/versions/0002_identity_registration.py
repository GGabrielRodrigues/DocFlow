"""Add institution registration fields and users.

Revision ID: 0002_identity_registration
Revises: 0001_initial
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_identity_registration"
down_revision: Union[str, Sequence[str], None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("institutions", sa.Column("institution_type", sa.String(length=50), nullable=True))
    op.add_column("institutions", sa.Column("cnpj", sa.String(length=14), nullable=True))
    op.add_column("institutions", sa.Column("email", sa.String(length=320), nullable=True))
    op.add_column("institutions", sa.Column("phone", sa.String(length=50), nullable=True))
    op.add_column("institutions", sa.Column("address", sa.String(length=500), nullable=True))
    op.execute(
        "UPDATE institutions SET institution_type = 'OTHER', cnpj = '00000000000000', "
        "email = 'migration@invalid.local' WHERE institution_type IS NULL"
    )
    with op.batch_alter_table("institutions") as batch:
        batch.alter_column("institution_type", nullable=False)
        batch.alter_column("cnpj", nullable=False)
        batch.alter_column("email", nullable=False)
        batch.create_unique_constraint("uq_institutions_cnpj", ["cnpj"])
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("institution_id", "email", name="uq_users_institution_email"),
    )
    op.create_index("ix_users_institution_id", "users", ["institution_id"])


def downgrade() -> None:
    op.drop_index("ix_users_institution_id", table_name="users")
    op.drop_table("users")
    with op.batch_alter_table("institutions") as batch:
        batch.drop_constraint("uq_institutions_cnpj", type_="unique")
        batch.drop_column("address")
        batch.drop_column("phone")
        batch.drop_column("email")
        batch.drop_column("cnpj")
        batch.drop_column("institution_type")

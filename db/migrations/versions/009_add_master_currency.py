"""Add currency preference to masters table

Revision ID: 009_add_master_currency
Revises: 008_add_master_language
Create Date: 2026-03-11
"""
from alembic import op
import sqlalchemy as sa

revision = "009_add_master_currency"
down_revision = "008_add_master_language"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "masters",
        sa.Column("currency", sa.String(8), nullable=False, server_default="RUB"),
    )


def downgrade() -> None:
    op.drop_column("masters", "currency")

"""Add language preference to masters table

Revision ID: 008_add_master_language
Revises: 007_service_price_nullable
Create Date: 2026-03-11
"""
from alembic import op
import sqlalchemy as sa

revision = "008_add_master_language"
down_revision = "007_service_price_nullable"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "masters",
        sa.Column("language", sa.String(8), nullable=False, server_default="ru"),
    )


def downgrade() -> None:
    op.drop_column("masters", "language")

"""Add consent fields to masters table

Revision ID: 005_add_master_consent
Revises: 004_add_client_notes
Create Date: 2026-03-11
"""
from alembic import op
import sqlalchemy as sa

revision = "005_add_master_consent"
down_revision = "004_add_client_notes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("masters", sa.Column(
        "consent_given", sa.Boolean, nullable=False, server_default="false"
    ))
    op.add_column("masters", sa.Column(
        "consent_at", sa.DateTime(timezone=False), nullable=True
    ))


def downgrade() -> None:
    op.drop_column("masters", "consent_given")
    op.drop_column("masters", "consent_at")

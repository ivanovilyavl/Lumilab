"""Add client consent fields to bookings table

Revision ID: 006_add_booking_consent
Revises: 005_add_master_consent
Create Date: 2026-03-11
"""
from alembic import op
import sqlalchemy as sa

revision = "006_add_booking_consent"
down_revision = "005_add_master_consent"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("bookings", sa.Column(
        "client_consent_given", sa.Boolean, nullable=False, server_default="false"
    ))
    op.add_column("bookings", sa.Column(
        "client_consent_at", sa.DateTime(timezone=False), nullable=True
    ))


def downgrade() -> None:
    op.drop_column("bookings", "client_consent_given")
    op.drop_column("bookings", "client_consent_at")

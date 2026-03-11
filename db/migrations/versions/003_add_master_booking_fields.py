"""Add master-created booking fields

Revision ID: 003_add_master_booking_fields
Revises: 002_add_qa_items
Create Date: 2026-03-11
"""
from alembic import op
import sqlalchemy as sa

revision = "003_add_master_booking_fields"
down_revision = "002_add_qa_items"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("bookings", sa.Column("client_notes", sa.String(256), nullable=True))
    op.add_column("bookings", sa.Column("is_recurring", sa.Boolean, server_default="false", nullable=False))
    op.add_column("bookings", sa.Column("recurrence_end_date", sa.Date, nullable=True))


def downgrade() -> None:
    op.drop_column("bookings", "recurrence_end_date")
    op.drop_column("bookings", "is_recurring")
    op.drop_column("bookings", "client_notes")

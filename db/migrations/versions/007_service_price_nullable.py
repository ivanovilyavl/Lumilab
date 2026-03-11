"""Make service price nullable (price by agreement)

Revision ID: 007_service_price_nullable
Revises: 006_add_booking_consent
Create Date: 2026-03-11
"""
from alembic import op
import sqlalchemy as sa

revision = "007_service_price_nullable"
down_revision = "006_add_booking_consent"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("services", "price", existing_type=sa.Integer(), nullable=True)


def downgrade() -> None:
    # Set NULL prices to 0 before making non-nullable
    op.execute("UPDATE services SET price = 0 WHERE price IS NULL")
    op.alter_column("services", "price", existing_type=sa.Integer(), nullable=False)

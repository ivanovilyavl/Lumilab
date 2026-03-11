"""Add client_notes table for per-master client comments

Revision ID: 004_add_client_notes
Revises: 003_add_master_booking_fields
Create Date: 2026-03-11
"""
from alembic import op
import sqlalchemy as sa

revision = "004_add_client_notes"
down_revision = "003_add_master_booking_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "client_notes",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("master_id", sa.BigInteger, sa.ForeignKey("masters.id", ondelete="CASCADE"), nullable=False),
        sa.Column("client_key", sa.String(128), nullable=False),  # tg_hash or "manual:{pseudo}"
        sa.Column("note", sa.Text, nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.text("NOW()"), onupdate=sa.text("NOW()")),
        sa.UniqueConstraint("master_id", "client_key", name="uq_client_note_master_key"),
    )


def downgrade() -> None:
    op.drop_table("client_notes")

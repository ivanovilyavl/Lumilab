"""Add qa_items table

Revision ID: 002_add_qa_items
Revises: 001_initial
Create Date: 2026-03-10
"""
from alembic import op
import sqlalchemy as sa

revision = "002_add_qa_items"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "qa_items",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("master_id", sa.BigInteger, sa.ForeignKey("masters.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question", sa.String(256), nullable=False),
        sa.Column("answer", sa.Text, nullable=False),
        sa.Column("sort_order", sa.Integer, server_default="0"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("idx_qa_items_master", "qa_items", ["master_id"])


def downgrade() -> None:
    op.drop_index("idx_qa_items_master", table_name="qa_items")
    op.drop_table("qa_items")

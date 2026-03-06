"""Initial schema with anonymity support

Revision ID: 001_initial
Revises:
Create Date: 2026-03-06
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Masters
    op.create_table(
        "masters",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("telegram_id", sa.BigInteger, unique=True, nullable=False),
        sa.Column("username", sa.String(64), unique=True, nullable=False),
        sa.Column("display_name", sa.String(128), nullable=True),
        sa.Column("bio", sa.Text),
        sa.Column("photo_file_id", sa.String(256)),
        sa.Column("niche", sa.String(64)),
        sa.Column("timezone", sa.String(64), server_default="Europe/Moscow"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("is_onboarded", sa.Boolean, server_default="false"),
        sa.Column("subscription_status", sa.String(32), server_default="trial"),
        sa.Column("trial_ends_at", sa.DateTime),
        sa.Column("subscription_ends_at", sa.DateTime),
        sa.Column("tribute_subscriber_id", sa.String(128)),
        sa.Column("referrer_id", sa.BigInteger, sa.ForeignKey("masters.id")),
        sa.Column("referral_code", sa.String(32), unique=True, nullable=False),
        sa.Column("referral_bonus_days", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    # Services
    op.create_table(
        "services",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("master_id", sa.BigInteger, sa.ForeignKey("masters.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("price", sa.Integer, nullable=False),
        sa.Column("duration_min", sa.Integer, nullable=False),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("sort_order", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # Schedule Templates
    op.create_table(
        "schedule_templates",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("master_id", sa.BigInteger, sa.ForeignKey("masters.id", ondelete="CASCADE"), nullable=False),
        sa.Column("day_of_week", sa.SmallInteger, nullable=False),
        sa.Column("start_time", sa.Time, nullable=False),
        sa.Column("end_time", sa.Time, nullable=False),
        sa.Column("slot_step_min", sa.Integer, server_default="30"),
        sa.Column("is_working", sa.Boolean, server_default="true"),
    )
    op.create_index("uq_master_day", "schedule_templates", ["master_id", "day_of_week"], unique=True)

    # Schedule Overrides
    op.create_table(
        "schedule_overrides",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("master_id", sa.BigInteger, sa.ForeignKey("masters.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("is_working", sa.Boolean, nullable=False),
        sa.Column("start_time", sa.Time),
        sa.Column("end_time", sa.Time),
        sa.Column("note", sa.String(256)),
    )
    op.create_index("uq_master_date", "schedule_overrides", ["master_id", "date"], unique=True)

    # Bookings (anonymized — no client PII)
    op.create_table(
        "bookings",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("master_id", sa.BigInteger, sa.ForeignKey("masters.id"), nullable=False),
        sa.Column("service_id", sa.BigInteger, sa.ForeignKey("services.id"), nullable=False),
        sa.Column("client_pseudo", sa.String(64), nullable=False),
        sa.Column("client_tg_hash", sa.String(64)),
        sa.Column("booking_date", sa.Date, nullable=False),
        sa.Column("start_time", sa.Time, nullable=False),
        sa.Column("end_time", sa.Time, nullable=False),
        sa.Column("status", sa.String(32), server_default="pending"),
        sa.Column("cancel_reason", sa.Text),
        sa.Column("reminder_24h_sent", sa.Boolean, server_default="false"),
        sa.Column("reminder_2h_sent", sa.Boolean, server_default="false"),
        sa.Column("source", sa.String(32), server_default="miniapp"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("idx_bookings_master_date", "bookings", ["master_id", "booking_date"])
    op.create_index("idx_bookings_status", "bookings", ["status"])
    op.create_index("idx_bookings_reminders", "bookings", ["reminder_24h_sent", "booking_date"])

    # Client Aliases (pseudonym per client+master pair)
    op.create_table(
        "client_aliases",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("tg_hash", sa.String(64), nullable=False),
        sa.Column("master_id", sa.BigInteger, sa.ForeignKey("masters.id", ondelete="CASCADE"), nullable=False),
        sa.Column("pseudo", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint("tg_hash", "master_id", name="uq_client_alias_tg_master"),
    )

    # Bot Messages (anonymous relay, TTL 7 days)
    op.create_table(
        "bot_messages",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("booking_id", sa.BigInteger, sa.ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_role", sa.String(16), nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # Referrals
    op.create_table(
        "referrals",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("referrer_id", sa.BigInteger, sa.ForeignKey("masters.id"), nullable=False),
        sa.Column("referred_id", sa.BigInteger, sa.ForeignKey("masters.id"), nullable=False, unique=True),
        sa.Column("bonus_applied", sa.Boolean, server_default="false"),
        sa.Column("bonus_days", sa.Integer, server_default="7"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # Payments
    op.create_table(
        "payments",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("master_id", sa.BigInteger, sa.ForeignKey("masters.id"), nullable=False),
        sa.Column("tribute_payment_id", sa.String(128), unique=True),
        sa.Column("amount_rub", sa.Integer, nullable=False),
        sa.Column("status", sa.String(32)),
        sa.Column("period_start", sa.DateTime),
        sa.Column("period_end", sa.DateTime),
        sa.Column("raw_webhook", JSONB),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # Events
    op.create_table(
        "events",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("master_id", sa.BigInteger, sa.ForeignKey("masters.id")),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("payload", JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("idx_events_type_date", "events", ["event_type", "created_at"])
    op.create_index("idx_events_master", "events", ["master_id", "created_at"])


def downgrade() -> None:
    op.drop_table("events")
    op.drop_table("payments")
    op.drop_table("referrals")
    op.drop_table("bot_messages")
    op.drop_table("client_aliases")
    op.drop_table("bookings")
    op.drop_table("schedule_overrides")
    op.drop_table("schedule_templates")
    op.drop_table("services")
    op.drop_table("masters")

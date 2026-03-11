from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class Master(Base):
    __tablename__ = "masters"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(128))
    bio: Mapped[str | None] = mapped_column(Text)
    photo_file_id: Mapped[str | None] = mapped_column(String(256))
    niche: Mapped[str | None] = mapped_column(String(64))
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/Moscow")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_onboarded: Mapped[bool] = mapped_column(Boolean, default=False)

    # Consent
    consent_given: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Subscription
    subscription_status: Mapped[str] = mapped_column(String(32), default="trial")
    trial_ends_at: Mapped[datetime | None] = mapped_column()
    subscription_ends_at: Mapped[datetime | None] = mapped_column()
    tribute_subscriber_id: Mapped[str | None] = mapped_column(String(128))

    # Referral
    referrer_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("masters.id"))
    referral_code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    referral_bonus_days: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    # Relationships
    services: Mapped[list["Service"]] = relationship(back_populates="master", cascade="all, delete-orphan")
    schedule_templates: Mapped[list["ScheduleTemplate"]] = relationship(
        back_populates="master", cascade="all, delete-orphan"
    )
    schedule_overrides: Mapped[list["ScheduleOverride"]] = relationship(
        back_populates="master", cascade="all, delete-orphan"
    )
    bookings: Mapped[list["Booking"]] = relationship(back_populates="master")
    qa_items: Mapped[list["QAItem"]] = relationship(back_populates="master", cascade="all, delete-orphan")


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    master_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("masters.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_min: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    master: Mapped["Master"] = relationship(back_populates="services")


class ScheduleTemplate(Base):
    __tablename__ = "schedule_templates"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    master_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("masters.id", ondelete="CASCADE"), nullable=False)
    day_of_week: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 0=Mon, 6=Sun
    start_time = mapped_column(Time, nullable=False)
    end_time = mapped_column(Time, nullable=False)
    slot_step_min: Mapped[int] = mapped_column(Integer, default=30)
    is_working: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (Index("uq_master_day", "master_id", "day_of_week", unique=True),)

    master: Mapped["Master"] = relationship(back_populates="schedule_templates")


class ScheduleOverride(Base):
    __tablename__ = "schedule_overrides"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    master_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("masters.id", ondelete="CASCADE"), nullable=False)
    date = mapped_column(Date, nullable=False)
    is_working: Mapped[bool] = mapped_column(Boolean, nullable=False)
    start_time = mapped_column(Time)
    end_time = mapped_column(Time)
    note: Mapped[str | None] = mapped_column(String(256))

    __table_args__ = (Index("uq_master_date", "master_id", "date", unique=True),)

    master: Mapped["Master"] = relationship(back_populates="schedule_overrides")


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    master_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("masters.id"), nullable=False)
    service_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("services.id"), nullable=False)

    # Anonymous client data (no PII stored)
    client_pseudo: Mapped[str] = mapped_column(String(64), nullable=False)
    client_tg_hash: Mapped[str | None] = mapped_column(String(64))

    # Time
    booking_date = mapped_column(Date, nullable=False)
    start_time = mapped_column(Time, nullable=False)
    end_time = mapped_column(Time, nullable=False)

    # Client consent (set when booking is created via miniapp after consent screen)
    client_consent_given: Mapped[bool] = mapped_column(Boolean, default=False)
    client_consent_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(32), default="pending")
    cancel_reason: Mapped[str | None] = mapped_column(Text)

    # Reminders
    reminder_24h_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    reminder_2h_sent: Mapped[bool] = mapped_column(Boolean, default=False)

    source: Mapped[str] = mapped_column(String(32), default="miniapp")

    # Master-created bookings
    client_notes: Mapped[str | None] = mapped_column(String(256))  # e.g. phone number
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    recurrence_end_date = mapped_column(Date, nullable=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_bookings_master_date", "master_id", "booking_date"),
        Index("idx_bookings_status", "status"),
        Index("idx_bookings_reminders", "reminder_24h_sent", "booking_date"),
    )

    master: Mapped["Master"] = relationship(back_populates="bookings")
    service: Mapped["Service"] = relationship()
    messages: Mapped[list["BotMessage"]] = relationship(back_populates="booking", cascade="all, delete-orphan")


class ClientAlias(Base):
    __tablename__ = "client_aliases"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tg_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    master_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("masters.id", ondelete="CASCADE"), nullable=False)
    pseudo: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    __table_args__ = (
        UniqueConstraint("tg_hash", "master_id", name="uq_client_alias_tg_master"),
    )


class BotMessage(Base):
    __tablename__ = "bot_messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    booking_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False)
    from_role: Mapped[str] = mapped_column(String(16), nullable=False)  # 'master' | 'client'
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    booking: Mapped["Booking"] = relationship(back_populates="messages")


class QAItem(Base):
    __tablename__ = "qa_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    master_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("masters.id", ondelete="CASCADE"), nullable=False)
    question: Mapped[str] = mapped_column(String(256), nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    master: Mapped["Master"] = relationship(back_populates="qa_items")


class ClientNote(Base):
    """Per-master comment on a client. client_key = tg_hash or 'manual:{pseudo}'."""
    __tablename__ = "client_notes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    master_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("masters.id", ondelete="CASCADE"), nullable=False)
    client_key: Mapped[str] = mapped_column(String(128), nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("master_id", "client_key", name="uq_client_note_master_key"),
    )


class Referral(Base):
    __tablename__ = "referrals"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    referrer_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("masters.id"), nullable=False)
    referred_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("masters.id"), nullable=False, unique=True)
    bonus_applied: Mapped[bool] = mapped_column(Boolean, default=False)
    bonus_days: Mapped[int] = mapped_column(Integer, default=7)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    master_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("masters.id"), nullable=False)
    tribute_payment_id: Mapped[str | None] = mapped_column(String(128), unique=True)
    amount_rub: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str | None] = mapped_column(String(32))
    period_start: Mapped[datetime | None] = mapped_column()
    period_end: Mapped[datetime | None] = mapped_column()
    raw_webhook = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    master_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("masters.id"))
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    __table_args__ = (
        Index("idx_events_type_date", "event_type", "created_at"),
        Index("idx_events_master", "master_id", "created_at"),
    )

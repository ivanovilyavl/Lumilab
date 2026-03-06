import asyncio
import logging
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from worker.celery_app import app
from db.models import Booking, Master, Service

logger = logging.getLogger(__name__)


def _get_bot():
    """Lazy import to avoid circular dependency."""
    from aiogram import Bot
    from aiogram.enums import ParseMode
    from shared.config import settings
    return Bot(token=settings.bot_token, parse_mode=ParseMode.HTML)


async def _find_client_tg_id(booking: Booking) -> int | None:
    """Lookup client telegram_id from tg_hash via Redis cache."""
    if not booking.client_tg_hash:
        return None
    try:
        from redis.asyncio import from_url
        from shared.config import settings
        redis = from_url(settings.redis_url)
        tg_id_bytes = await redis.get(f"tghash:{booking.client_tg_hash}")
        await redis.aclose()
        if tg_id_bytes:
            return int(tg_id_bytes)
    except Exception:
        pass
    return None


async def _send_reminder_24h():
    from db.session import async_session
    from bot.keyboards.common import client_cancel_kb

    now = datetime.now(timezone.utc)
    window_start = now + timedelta(hours=22)
    window_end = now + timedelta(hours=26)

    async with async_session() as db:
        result = await db.execute(
            select(Booking)
            .options(selectinload(Booking.service), selectinload(Booking.master))
            .where(
                Booking.status == "confirmed",
                Booking.reminder_24h_sent == False,
                Booking.booking_date >= window_start.date(),
                Booking.booking_date <= window_end.date(),
            )
        )
        bookings = list(result.scalars().all())

        bot = _get_bot()
        sent = 0

        for b in bookings:
            booking_dt = datetime.combine(b.booking_date, b.start_time, tzinfo=timezone.utc)
            if not (window_start <= booking_dt <= window_end):
                continue

            client_tg_id = await _find_client_tg_id(b)
            if client_tg_id:
                try:
                    await bot.send_message(
                        client_tg_id,
                        f"⏰ Напоминание о записи\n\n"
                        f"👤 {b.master.display_name or 'Мастер'}\n"
                        f"💅 {b.service.name} · {b.service.duration_min} мин · {b.service.price} ₽\n"
                        f"📆 Завтра в {b.start_time.strftime('%H:%M')}",
                        reply_markup=client_cancel_kb(b.id),
                    )
                    sent += 1
                except Exception as e:
                    logger.warning(f"Failed to send 24h reminder for booking {b.id}: {e}")

            b.reminder_24h_sent = True

        await db.commit()
        await bot.session.close()
        logger.info(f"24h reminders: {sent} sent out of {len(bookings)} bookings")


async def _send_reminder_2h():
    from db.session import async_session
    from bot.keyboards.common import client_cancel_kb

    now = datetime.now(timezone.utc)
    window_start = now + timedelta(hours=1, minutes=45)
    window_end = now + timedelta(hours=2, minutes=15)

    async with async_session() as db:
        result = await db.execute(
            select(Booking)
            .options(selectinload(Booking.service), selectinload(Booking.master))
            .where(
                Booking.status == "confirmed",
                Booking.reminder_2h_sent == False,
                Booking.booking_date == now.date(),
            )
        )
        bookings = list(result.scalars().all())

        bot = _get_bot()
        sent = 0

        for b in bookings:
            booking_dt = datetime.combine(b.booking_date, b.start_time, tzinfo=timezone.utc)
            if not (window_start <= booking_dt <= window_end):
                continue

            client_tg_id = await _find_client_tg_id(b)
            if client_tg_id:
                try:
                    await bot.send_message(
                        client_tg_id,
                        f"⏰ Через 2 часа — ваша запись!\n\n"
                        f"👤 {b.master.display_name or 'Мастер'} · {b.service.name}\n"
                        f"🕐 Сегодня в {b.start_time.strftime('%H:%M')}",
                        reply_markup=client_cancel_kb(b.id),
                    )
                    sent += 1
                except Exception as e:
                    logger.warning(f"Failed to send 2h reminder for booking {b.id}: {e}")

            b.reminder_2h_sent = True

        await db.commit()
        await bot.session.close()
        logger.info(f"2h reminders: {sent} sent out of {len(bookings)} bookings")


async def _auto_cancel_pending():
    """Auto-cancel pending bookings not confirmed within 12 hours.

    Exception: if 12h expires less than 2h before appointment,
    cancel 2h before appointment instead.
    """
    from db.session import async_session
    from db.models import Event

    now = datetime.now(timezone.utc)

    async with async_session() as db:
        result = await db.execute(
            select(Booking)
            .options(selectinload(Booking.service), selectinload(Booking.master))
            .where(
                Booking.status == "pending",
            )
        )
        bookings = list(result.scalars().all())

        bot = _get_bot()
        cancelled = 0

        for b in bookings:
            booking_dt = datetime.combine(b.booking_date, b.start_time, tzinfo=timezone.utc)
            created_at = b.created_at.replace(tzinfo=timezone.utc) if b.created_at.tzinfo is None else b.created_at
            twelve_h_deadline = created_at + timedelta(hours=12)
            two_h_before = booking_dt - timedelta(hours=2)

            # Determine actual cancel time
            if twelve_h_deadline > two_h_before:
                # 12h would be too late — cancel at 2h before appointment
                cancel_at = two_h_before
            else:
                cancel_at = twelve_h_deadline

            if now < cancel_at:
                continue  # Not time yet

            b.status = "cancelled"
            b.cancel_reason = "Автоотмена: мастер не подтвердил вовремя"
            db.add(Event(
                master_id=b.master_id,
                event_type="booking_auto_cancelled",
                payload={"booking_id": b.id},
            ))
            cancelled += 1

            # Notify client
            client_tg_id = await _find_client_tg_id(b)
            if client_tg_id:
                try:
                    await bot.send_message(
                        client_tg_id,
                        f"😔 Мастер не успел подтвердить вашу запись.\n"
                        f"Слот освободился — можете записаться снова.",
                    )
                except Exception:
                    pass

            # Notify master
            if b.master:
                try:
                    await bot.send_message(
                        b.master.telegram_id,
                        f"⚠️ Запись «{b.client_pseudo}» на "
                        f"{b.booking_date.strftime('%d.%m')} в {b.start_time.strftime('%H:%M')} "
                        f"автоматически отменена — не подтверждена за 12 часов.",
                    )
                except Exception:
                    pass

        await db.commit()
        await bot.session.close()
        logger.info(f"Auto-cancel: {cancelled} pending bookings cancelled")


async def _cleanup_old_messages():
    """Delete bot_messages for bookings older than 7 days after booking_date."""
    from db.session import async_session
    from db.models import BotMessage

    cutoff = date.today() - timedelta(days=7)

    async with async_session() as db:
        result = await db.execute(
            select(BotMessage)
            .join(Booking, BotMessage.booking_id == Booking.id)
            .where(Booking.booking_date < cutoff)
        )
        messages = list(result.scalars().all())
        for msg in messages:
            await db.delete(msg)
        await db.commit()
        if messages:
            logger.info(f"Cleanup: deleted {len(messages)} old bot messages")


@app.task(name="worker.tasks.reminders.send_reminders_24h")
def send_reminders_24h():
    asyncio.run(_send_reminder_24h())


@app.task(name="worker.tasks.reminders.send_reminders_2h")
def send_reminders_2h():
    asyncio.run(_send_reminder_2h())


@app.task(name="worker.tasks.reminders.auto_cancel_pending")
def auto_cancel_pending():
    asyncio.run(_auto_cancel_pending())


@app.task(name="worker.tasks.reminders.cleanup_old_messages")
def cleanup_old_messages():
    asyncio.run(_cleanup_old_messages())

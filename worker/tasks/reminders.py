import asyncio
import logging
from datetime import date, datetime, time, timedelta

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from worker.celery_app import app
from db.models import Booking, Master, Service
from shared.i18n import t

logger = logging.getLogger(__name__)


def _get_bot():
    """Lazy import to avoid circular dependency."""
    from aiogram import Bot
    from aiogram.client.default import DefaultBotProperties
    from aiogram.enums import ParseMode
    from shared.config import settings
    return Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


async def _find_client_tg_id(booking: Booking) -> int | None | bool:
    """Lookup client telegram_id from tg_hash via Redis cache.

    Returns:
        int   — telegram_id found, can send
        None  — booking has no tg_hash (anonymous client), nothing to send
        False — tg_hash exists but Redis lookup failed (transient); caller should NOT mark as sent
    """
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
        # Key absent (expired or never written) — treat as permanent miss
        return None
    except Exception as e:
        logger.warning(f"Redis lookup failed for booking {booking.id}: {e}")
        return False  # transient failure — do not mark as sent


async def _send_reminder_24h():
    from db.session import async_session
    from bot.keyboards.common import client_cancel_kb
    from shared.i18n import fmt_price as _fmt_price

    now = datetime.utcnow()
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

        if not bookings:
            logger.info("24h reminders: no eligible bookings")
            return

        bot = _get_bot()
        sent = 0

        try:
            for b in bookings:
                booking_dt = datetime.combine(b.booking_date, b.start_time)
                if not (window_start <= booking_dt <= window_end):
                    continue

                tg_result = await _find_client_tg_id(b)
                if tg_result is False:
                    # Transient Redis error — skip this booking, retry next run
                    continue

                # tg_result is None (anonymous) or int (telegram_id found)
                if tg_result is not None and b.service is not None:
                    try:
                        lang = getattr(b.master, "language", "ru") or "ru"
                        currency = getattr(b.master, "currency", "RUB") or "RUB"
                        min_unit = t(lang, "min_unit")
                        price_str = _fmt_price(b.service.price, currency, lang)
                        await bot.send_message(
                            tg_result,
                            t(lang, "reminder_24h",
                              master=b.master.display_name or "Мастер",
                              service=b.service.name,
                              duration=f"{b.service.duration_min} {min_unit}",
                              price=price_str,
                              time=b.start_time.strftime("%H:%M")),
                            reply_markup=client_cancel_kb(b.id),
                        )
                        sent += 1
                    except Exception as e:
                        logger.warning(f"Failed to send 24h reminder for booking {b.id}: {e}")
                        continue  # do not mark as sent — retry next run

                # Mark as sent: anonymous client (tg_result is None) or message delivered
                b.reminder_24h_sent = True

            await db.commit()
        finally:
            await bot.session.close()

        logger.info(f"24h reminders: {sent} sent out of {len(bookings)} bookings")


async def _send_reminder_2h():
    from db.session import async_session
    from bot.keyboards.common import client_cancel_kb

    now = datetime.utcnow()
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

        if not bookings:
            logger.info("2h reminders: no eligible bookings")
            return

        bot = _get_bot()
        sent = 0

        try:
            for b in bookings:
                booking_dt = datetime.combine(b.booking_date, b.start_time)
                if not (window_start <= booking_dt <= window_end):
                    continue

                tg_result = await _find_client_tg_id(b)
                if tg_result is False:
                    # Transient Redis error — skip, retry next run
                    continue

                if tg_result is not None and b.service is not None:
                    try:
                        lang = getattr(b.master, "language", "ru") or "ru"
                        await bot.send_message(
                            tg_result,
                            t(lang, "reminder_2h",
                              master=b.master.display_name or "Мастер",
                              service=b.service.name,
                              time=b.start_time.strftime("%H:%M")),
                            reply_markup=client_cancel_kb(b.id),
                        )
                        sent += 1
                    except Exception as e:
                        logger.warning(f"Failed to send 2h reminder for booking {b.id}: {e}")
                        continue  # do not mark as sent — retry next run

                b.reminder_2h_sent = True

            await db.commit()
        finally:
            await bot.session.close()

        logger.info(f"2h reminders: {sent} sent out of {len(bookings)} bookings")


async def _auto_cancel_pending():
    """Auto-cancel pending bookings not confirmed within 12 hours.

    Exception: if 12h expires less than 2h before appointment,
    cancel 2h before appointment instead.
    """
    from db.session import async_session
    from db.models import Event

    now = datetime.utcnow()

    async with async_session() as db:
        result = await db.execute(
            select(Booking)
            .options(selectinload(Booking.service), selectinload(Booking.master))
            .where(
                Booking.status == "pending",
            )
        )
        bookings = list(result.scalars().all())

        if not bookings:
            logger.info("Auto-cancel: no pending bookings")
            return

        bot = _get_bot()
        cancelled = 0

        try:
            for b in bookings:
                booking_dt = datetime.combine(b.booking_date, b.start_time)
                created_at = b.created_at
                twelve_h_deadline = created_at + timedelta(hours=12)
                two_h_before = booking_dt - timedelta(hours=2)

                # If the appointment is less than 2 hours away from now, skip auto-cancel:
                # the master still has time to confirm manually before the appointment starts.
                if now >= two_h_before:
                    continue

                # Determine actual cancel time: whichever comes first
                cancel_at = min(twelve_h_deadline, two_h_before)

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
                tg_result = await _find_client_tg_id(b)
                if isinstance(tg_result, int):
                    try:
                        await bot.send_message(
                            tg_result,
                            "😔 Мастер не успел подтвердить вашу запись.\n"
                            "Слот освободился — можете записаться снова.",
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
        finally:
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
            db.delete(msg)
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

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


async def _send_reminder_24h():
    from db.session import async_session

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
            # More precise check: combine date + time
            booking_dt = datetime.combine(b.booking_date, b.start_time, tzinfo=timezone.utc)
            if not (window_start <= booking_dt <= window_end):
                continue

            if b.client_telegram_id:
                try:
                    await bot.send_message(
                        b.client_telegram_id,
                        f"⏰ Напоминание о записи\n\n"
                        f"👤 Мастер: {b.master.display_name}\n"
                        f"💅 Услуга: {b.service.name}\n"
                        f"📅 Завтра в {b.start_time.strftime('%H:%M')}\n\n"
                        f"Если нужно отменить — напишите мастеру.",
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

            if b.client_telegram_id:
                try:
                    await bot.send_message(
                        b.client_telegram_id,
                        f"⏰ Через 2 часа — ваша запись!\n\n"
                        f"👤 {b.master.display_name} · {b.service.name}\n"
                        f"🕐 Сегодня в {b.start_time.strftime('%H:%M')}",
                    )
                    sent += 1
                except Exception as e:
                    logger.warning(f"Failed to send 2h reminder for booking {b.id}: {e}")

            b.reminder_2h_sent = True

        await db.commit()
        await bot.session.close()
        logger.info(f"2h reminders: {sent} sent out of {len(bookings)} bookings")


@app.task(name="worker.tasks.reminders.send_reminders_24h")
def send_reminders_24h():
    asyncio.run(_send_reminder_24h())


@app.task(name="worker.tasks.reminders.send_reminders_2h")
def send_reminders_2h():
    asyncio.run(_send_reminder_2h())

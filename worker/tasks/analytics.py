import asyncio
import logging
from datetime import datetime, timedelta

from sqlalchemy import func, select, text

from worker.celery_app import app
from db.models import Event

logger = logging.getLogger(__name__)


async def _aggregate_analytics():
    """Aggregate hourly event counts for dashboard queries."""
    from db.session import async_session

    now = datetime.utcnow()
    hour_ago = now - timedelta(hours=1)

    async with async_session() as db:
        result = await db.execute(
            select(Event.event_type, func.count().label("cnt"))
            .where(Event.created_at >= hour_ago)
            .group_by(Event.event_type)
        )
        counts = {row.event_type: row.cnt for row in result.all()}
        logger.info(f"Hourly analytics: {counts}")


async def _send_weekly_digest():
    """Send weekly digest to analytics bot."""
    from db.session import async_session
    from shared.config import settings
    from aiogram import Bot
    from aiogram.enums import ParseMode

    if not settings.analytics_bot_token:
        return

    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)

    async with async_session() as db:
        result = await db.execute(
            select(Event.event_type, func.count().label("cnt"))
            .where(Event.created_at >= week_ago)
            .group_by(Event.event_type)
        )
        counts = {row.event_type: row.cnt for row in result.all()}

    text_lines = [
        "📊 <b>Недельный дайджест</b>\n",
        f"👤 Новых мастеров: +{counts.get('master_registered', 0)}",
        f"✅ Онбординг: +{counts.get('master_onboarded', 0)}",
        f"📅 Записей: +{counts.get('booking_created', 0)}",
        f"✅ Подтверждено: +{counts.get('booking_confirmed', 0)}",
        f"💰 Подписок: +{counts.get('subscription_activated', 0)}",
        f"🎁 Рефералов: +{counts.get('referral_used', 0)}",
    ]

    from aiogram.client.default import DefaultBotProperties
    bot = Bot(token=settings.analytics_bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    for admin_id in settings.admin_ids:
        try:
            await bot.send_message(admin_id, "\n".join(text_lines))
        except Exception as e:
            logger.warning(f"Failed to send digest to {admin_id}: {e}")
    await bot.session.close()


@app.task(name="worker.tasks.analytics.aggregate_analytics")
def aggregate_analytics():
    asyncio.run(_aggregate_analytics())


@app.task(name="worker.tasks.analytics.send_weekly_digest")
def send_weekly_digest():
    asyncio.run(_send_weekly_digest())

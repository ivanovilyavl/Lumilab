import logging

logger = logging.getLogger(__name__)


async def send_alert(text: str) -> None:
    """Send a critical alert to all analytics bot admins."""
    from aiogram import Bot
    from aiogram.client.default import DefaultBotProperties
    from aiogram.enums import ParseMode
    from shared.config import settings

    if not settings.analytics_bot_token or not settings.admin_ids:
        logger.warning("send_alert: analytics_bot_token or admin_ids not configured, skipping")
        return

    bot = Bot(
        token=settings.analytics_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    try:
        for admin_id in settings.admin_ids:
            try:
                await bot.send_message(admin_id, text)
            except Exception as e:
                logger.warning(f"send_alert: failed to notify admin {admin_id}: {e}")
    finally:
        await bot.session.close()

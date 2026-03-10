import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import MenuButtonWebApp, WebAppInfo
from sqlalchemy import select

from bot.handlers import start, profile, services, schedule, bookings, subscription, referral, mylink, help
from bot.middlewares.auth import AuthMiddleware
from bot.middlewares.subscription import SubscriptionMiddleware
from db.models import Master
from db.session import async_session
from shared.config import settings

logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)


async def restore_master_menu_buttons(bot: Bot) -> None:
    """Ensure all onboarded masters have their personalised menu button set."""
    async with async_session() as session:
        result = await session.execute(
            select(Master).where(Master.is_onboarded.is_(True))
        )
        masters = result.scalars().all()

    logger.info("Restoring menu buttons for %d masters…", len(masters))
    for master in masters:
        try:
            await bot.set_chat_menu_button(
                chat_id=master.telegram_id,
                menu_button=MenuButtonWebApp(
                    text="Открыть",
                    web_app=WebAppInfo(url=f"{settings.miniapp_url}?master={master.username}"),
                ),
            )
            await asyncio.sleep(0.05)  # stay well within Telegram rate limits
        except Exception as exc:
            logger.warning("Could not set menu button for master %s: %s", master.telegram_id, exc)


async def main():
    storage = RedisStorage.from_url(settings.redis_url)
    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=storage)

    # Middlewares (order matters: auth first, then subscription check)
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())
    dp.message.middleware(SubscriptionMiddleware())
    dp.callback_query.middleware(SubscriptionMiddleware())

    # Register routers
    dp.include_router(start.router)
    dp.include_router(profile.router)
    dp.include_router(services.router)
    dp.include_router(schedule.router)
    dp.include_router(bookings.router)
    dp.include_router(subscription.router)
    dp.include_router(referral.router)
    dp.include_router(mylink.router)
    dp.include_router(help.router)

    # Set default Web App menu button (fallback for non-masters / unregistered users)
    await bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(
            text="Открыть",
            web_app=WebAppInfo(url=settings.miniapp_url),
        )
    )
    logger.info("Default menu button set to %s", settings.miniapp_url)

    # Restore personalised menu buttons for every onboarded master in the background
    asyncio.create_task(restore_master_menu_buttons(bot))

    logger.info("Bot starting...")
    await dp.start_polling(bot, drop_pending_updates=True)


if __name__ == "__main__":
    asyncio.run(main())

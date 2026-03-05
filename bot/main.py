import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from bot.handlers import start, profile, services, schedule, bookings, subscription, referral, mylink, help
from bot.middlewares.auth import AuthMiddleware
from bot.middlewares.subscription import SubscriptionMiddleware
from shared.config import settings

logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)


async def main():
    storage = RedisStorage.from_url(settings.redis_url)
    bot = Bot(token=settings.bot_token, parse_mode=ParseMode.HTML)
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

    logger.info("Bot starting...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from shared.config import settings

logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)


async def main():
    storage = RedisStorage.from_url(settings.redis_url)
    bot = Bot(token=settings.analytics_bot_token, parse_mode=ParseMode.HTML)
    dp = Dispatcher(storage=storage)

    # Handlers will be registered here
    # from analytics_bot.handlers import overview, users, revenue, funnels, referrals

    logger.info("Analytics bot starting...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

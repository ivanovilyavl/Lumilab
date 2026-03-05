import asyncio
import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware, Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import Message, TelegramObject

from analytics_bot.handlers import (
    bookings_stats,
    cohorts,
    export,
    funnels,
    master_info,
    niches,
    overview,
    referrals,
    revenue,
    users,
)
from db.session import async_session
from shared.config import settings

logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)


class AdminOnlyMiddleware(BaseMiddleware):
    """Allow only ANALYTICS_ADMIN_IDS, reject everyone else."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Message) and event.from_user:
            if event.from_user.id not in settings.admin_ids:
                await event.answer("Access denied.")
                return None
        return await handler(event, data)


class DbMiddleware(BaseMiddleware):
    """Injects db session into handler data."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with async_session() as session:
            data["db"] = session
            return await handler(event, data)


async def main():
    storage = RedisStorage.from_url(settings.redis_url)
    bot = Bot(token=settings.analytics_bot_token, parse_mode=ParseMode.HTML)
    dp = Dispatcher(storage=storage)

    # Middlewares
    dp.message.middleware(AdminOnlyMiddleware())
    dp.message.middleware(DbMiddleware())

    # Routers
    dp.include_router(overview.router)
    dp.include_router(users.router)
    dp.include_router(revenue.router)
    dp.include_router(funnels.router)
    dp.include_router(referrals.router)
    dp.include_router(niches.router)
    dp.include_router(cohorts.router)
    dp.include_router(bookings_stats.router)
    dp.include_router(master_info.router)
    dp.include_router(export.router)

    logger.info("Analytics bot starting...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

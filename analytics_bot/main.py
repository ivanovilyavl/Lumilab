import asyncio
import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware, Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import BotCommand, ErrorEvent, MenuButtonWebApp, Message, TelegramObject, WebAppInfo

from analytics_bot.handlers import (
    bookings_stats,
    cohorts,
    counts,
    export,
    feedback,
    funnels,
    master_info,
    niches,
    overview,
    panel,
    referrals,
    revenue,
    users,
)
from db.session import async_session
from shared.analytics import send_alert
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
    bot = Bot(token=settings.analytics_bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=storage)

    # Middlewares
    dp.message.middleware(AdminOnlyMiddleware())
    dp.message.middleware(DbMiddleware())

    # Routers
    dp.include_router(panel.router)
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
    dp.include_router(counts.router)
    dp.include_router(feedback.router)  # must be last — catches all reply messages

    # Error handler — logs and notifies admins via this bot itself
    @dp.error()
    async def error_handler(event: ErrorEvent) -> None:
        exc = event.exception
        logger.exception(f"Unhandled exception in analytics bot handler: {exc}")
        for admin_id in settings.admin_ids:
            try:
                await bot.send_message(
                    admin_id,
                    f"🔴 <b>Ошибка в аналитик-боте</b>\n\n"
                    f"<code>{type(exc).__name__}: {exc}</code>",
                )
            except Exception:
                pass

    # Shutdown notification — send via main bot so admins are notified even if analytics bot dies
    @dp.shutdown()
    async def on_shutdown(**kwargs) -> None:
        await send_alert("🛑 <b>Аналитик-бот остановлен</b>")

    # Set bot command menu
    await bot.set_my_commands([
        BotCommand(command="panel", description="Открыть панель аналитики"),
        BotCommand(command="stats", description="Сводка за сегодня / неделю"),
        BotCommand(command="users", description="Статистика пользователей"),
        BotCommand(command="revenue", description="Выручка и платежи"),
        BotCommand(command="masters", description="Топ мастеров"),
        BotCommand(command="bookings", description="Статистика записей"),
        BotCommand(command="funnels", description="Воронки"),
        BotCommand(command="cohorts", description="Когортный анализ"),
        BotCommand(command="export", description="Выгрузка данных в CSV"),
    ])

    # Set default menu button — WebApp panel
    admin_url = f"{settings.miniapp_url.rstrip('/')}/admin/"
    await bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(
            text="Панель",
            web_app=WebAppInfo(url=admin_url),
        )
    )
    logger.info("Analytics bot menu configured, panel URL: %s", admin_url)

    logger.info("Analytics bot starting...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

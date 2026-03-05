from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Master
from db.session import async_session


class AuthMiddleware(BaseMiddleware):
    """Injects db session and master object into handler data."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with async_session() as session:
            data["db"] = session

            # Get telegram_id from message or callback
            user = None
            if isinstance(event, Message) and event.from_user:
                user = event.from_user
            elif isinstance(event, CallbackQuery) and event.from_user:
                user = event.from_user

            if user:
                result = await session.execute(
                    select(Master).where(Master.telegram_id == user.id)
                )
                master = result.scalar_one_or_none()
                data["master"] = master

            return await handler(event, data)

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message

from redis.asyncio import Redis


class ThrottleMiddleware(BaseMiddleware):
    """Simple rate limiter: 1 message per second per user."""

    def __init__(self, redis: Redis, rate_limit: float = 1.0):
        self.redis = redis
        self.rate_limit = rate_limit

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message) or not event.from_user:
            return await handler(event, data)

        key = f"throttle:{event.from_user.id}"
        if await self.redis.exists(key):
            return None  # silently drop

        await self.redis.set(key, "1", ex=int(self.rate_limit))
        return await handler(event, data)

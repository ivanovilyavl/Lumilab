from datetime import datetime
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from db.models import Master
from shared.config import settings

# Commands allowed without active subscription
ALLOWED_COMMANDS = {"/start", "/help", "/subscription", "/reset"}
ALLOWED_TEXTS = {"❓ Помощь", "💳 Подписка"}
ALLOWED_CALLBACKS = {"payments_history"}


class SubscriptionMiddleware(BaseMiddleware):
    """
    Blocks commands if subscription is inactive.

    Access is allowed if any of:
    - subscription_status == 'trial' AND trial_ends_at > now()
    - subscription_status == 'active' AND subscription_ends_at > now()
    - referral_bonus_days > 0
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        master: Master | None = data.get("master")

        # No master yet (new user going through /start) — allow
        if not master:
            return await handler(event, data)

        # Check if command/text is in allowed list
        if isinstance(event, Message):
            text = (event.text or "").strip()
            if text.split("@")[0] in ALLOWED_COMMANDS or text in ALLOWED_TEXTS:
                return await handler(event, data)
        elif isinstance(event, CallbackQuery):
            if event.data in ALLOWED_CALLBACKS:
                return await handler(event, data)

        # Check subscription
        now = datetime.utcnow()
        has_access = False

        if master.subscription_status == "trial" and master.trial_ends_at and master.trial_ends_at > now:
            has_access = True
        elif master.subscription_status == "active" and master.subscription_ends_at and master.subscription_ends_at > now:
            has_access = True
        elif master.referral_bonus_days > 0:
            has_access = True

        if has_access:
            return await handler(event, data)

        # Blocked — show subscription message
        buttons = []
        if settings.tribute_subscription_url:
            buttons.append([
                InlineKeyboardButton(
                    text=f"💳 Оформить подписку — {settings.tribute_monthly_price_rub} ₽/мес",
                    url=settings.tribute_subscription_url,
                )
            ])

        block_text = (
            "⚠️ <b>Подписка неактивна</b>\n\n"
            "Для продолжения работы оформите подписку.\n"
            f"Стоимость: {settings.tribute_monthly_price_rub} ₽/мес"
        )

        if isinstance(event, Message):
            await event.answer(
                block_text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None,
            )
        elif isinstance(event, CallbackQuery):
            await event.answer("Подписка неактивна. Используйте /subscription", show_alert=True)

        return None

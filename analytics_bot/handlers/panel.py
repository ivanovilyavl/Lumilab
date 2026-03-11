from aiogram import Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo

from shared.config import settings

router = Router()


@router.message(Command("panel"))
async def cmd_panel(message: Message):
    """Open the admin WebApp panel."""
    url = f"{settings.miniapp_url.rstrip('/')}/admin/"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть панель",
                    web_app=WebAppInfo(url=url),
                )
            ]
        ]
    )
    await message.answer("Открыть панель аналитики:", reply_markup=keyboard)

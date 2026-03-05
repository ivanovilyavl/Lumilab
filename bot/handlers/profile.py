from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.start import log_event
from db.models import Master

router = Router()


@router.message(Command("profile"))
@router.message(F.text == "👤 Профиль")
async def cmd_profile(message: Message, db: AsyncSession, master: Master):
    niche_map = {
        "beauty": "💅 Бьюти",
        "tutor": "📚 Репетитор",
        "trainer": "🏋️ Тренер",
        "psychologist": "🧠 Психолог",
        "photo": "📷 Фото",
        "other": "🔧 Другое",
    }
    niche_text = niche_map.get(master.niche, master.niche or "—")

    text = (
        f"👤 <b>Ваш профиль</b>\n\n"
        f"<b>Имя:</b> {master.display_name}\n"
        f"<b>Username:</b> @{master.username}\n"
        f"<b>Сфера:</b> {niche_text}\n"
        f"<b>Описание:</b> {master.bio or '(не задано)'}\n\n"
        f"Для изменения профиля используйте команды:\n"
        f"/setname — изменить имя\n"
        f"/setbio — изменить описание\n"
        f"/setphoto — изменить фото"
    )
    await message.answer(text)

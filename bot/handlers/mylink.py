from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Master, Event

router = Router()


@router.message(Command("mylink"))
@router.message(F.text == "🔗 Моя ссылка")
async def cmd_mylink(message: Message, db: AsyncSession, master: Master):
    link = f"https://t.me/ZapisBOT?startapp={master.username}"

    db.add(Event(master_id=master.id, event_type="link_shared"))
    await db.commit()

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📤 Поделиться",
                    switch_inline_query=f"Запишись онлайн: {link}",
                ),
            ]
        ]
    )

    await message.answer(
        f"🔗 <b>Ваша ссылка для клиентов:</b>\n\n"
        f"<code>{link}</code>\n\n"
        f"Отправьте эту ссылку клиентам — они смогут записаться онлайн!",
        reply_markup=kb,
    )

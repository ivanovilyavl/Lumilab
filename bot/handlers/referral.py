from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Master, Referral
from shared.config import settings

router = Router()


@router.message(Command("referral"))
@router.message(F.text == "🎁 Рефералы")
async def cmd_referral(message: Message, db: AsyncSession, master: Master):
    ref_link = f"https://t.me/{settings.bot_username}?start=ref_{master.referral_code}"

    # Count referrals
    result = await db.execute(
        select(func.count()).select_from(Referral).where(Referral.referrer_id == master.id)
    )
    total_referrals = result.scalar() or 0

    result = await db.execute(
        select(func.count())
        .select_from(Referral)
        .where(Referral.referrer_id == master.id, Referral.bonus_applied == True)
    )
    completed = result.scalar() or 0

    text = (
        f"🎁 <b>Реферальная программа</b>\n\n"
        f"Приглашайте коллег и получайте <b>+7 дней</b> подписки за каждого!\n\n"
        f"🔗 Ваша ссылка:\n<code>{ref_link}</code>\n\n"
        f"📊 Приглашено: <b>{total_referrals}</b>\n"
        f"✅ Прошли онбординг: <b>{completed}</b>\n"
        f"🎁 Бонусных дней накоплено: <b>{master.referral_bonus_days}</b>"
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📋 Скопировать ссылку", callback_data="ref_copy"),
                InlineKeyboardButton(
                    text="📤 Поделиться",
                    switch_inline_query=f"Записывайся онлайн: {ref_link}",
                ),
            ]
        ]
    )

    await message.answer(text, reply_markup=kb)


@router.callback_query(F.data == "ref_copy")
async def ref_copy(callback, master: Master):
    ref_link = f"https://t.me/{settings.bot_username}?start=ref_{master.referral_code}"
    await callback.answer(f"Ссылка: {ref_link}", show_alert=True)

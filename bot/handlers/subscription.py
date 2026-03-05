from datetime import datetime, timezone

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Master, Payment
from shared.config import settings

router = Router()


def days_left(dt: datetime | None) -> int:
    if not dt:
        return 0
    now = datetime.now(timezone.utc)
    delta = dt - now
    return max(0, delta.days)


@router.message(Command("subscription"))
@router.message(F.text == "💳 Подписка")
async def cmd_subscription(message: Message, db: AsyncSession, master: Master):
    status = master.subscription_status

    if status == "trial":
        left = days_left(master.trial_ends_at)
        text = (
            f"💳 <b>Подписка</b>\n\n"
            f"📌 Статус: Пробный период\n"
            f"⏰ Осталось дней: <b>{left}</b>\n"
        )
    elif status == "active":
        left = days_left(master.subscription_ends_at)
        bonus = master.referral_bonus_days
        text = (
            f"💳 <b>Подписка</b>\n\n"
            f"📌 Статус: ✅ Активна\n"
            f"📅 До: {master.subscription_ends_at.strftime('%d.%m.%Y') if master.subscription_ends_at else '—'}\n"
        )
        if bonus > 0:
            text += f"🎁 Бонусных дней: {bonus}\n"
    else:
        text = (
            f"💳 <b>Подписка</b>\n\n"
            f"📌 Статус: ❌ Неактивна\n"
            f"Без подписки клиенты не смогут записаться.\n"
        )

    text += f"\n💰 Стоимость: {settings.tribute_monthly_price_rub} ₽/мес"

    buttons = []
    if settings.tribute_subscription_url:
        buttons.append([
            InlineKeyboardButton(
                text="💳 Оформить подписку",
                url=settings.tribute_subscription_url,
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="📜 История платежей", callback_data="payments_history")
    ])

    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@router.callback_query(F.data == "payments_history")
async def payments_history(callback, db: AsyncSession, master: Master):
    result = await db.execute(
        select(Payment)
        .where(Payment.master_id == master.id)
        .order_by(Payment.created_at.desc())
        .limit(10)
    )
    payments = list(result.scalars().all())

    if not payments:
        await callback.message.edit_text("📜 История платежей пуста.")
        await callback.answer()
        return

    lines = []
    for p in payments:
        status_icon = "✅" if p.status == "paid" else "❌"
        dt = p.created_at.strftime("%d.%m.%Y") if p.created_at else "—"
        lines.append(f"{status_icon} {dt} — {p.amount_rub} ₽")

    await callback.message.edit_text(
        "📜 <b>История платежей:</b>\n\n" + "\n".join(lines)
    )
    await callback.answer()

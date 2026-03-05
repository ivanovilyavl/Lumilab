from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Master, Booking, Event, Referral, Payment

router = Router()


@router.message(Command("master"))
async def cmd_master(message: Message, db: AsyncSession, command: CommandObject):
    if not command.args:
        await message.answer("Использование: /master {id}")
        return

    try:
        master_id = int(command.args.strip())
    except ValueError:
        await message.answer("ID должен быть числом")
        return

    master = await db.get(Master, master_id)
    if not master:
        await message.answer("Мастер не найден")
        return

    # Bookings count
    result = await db.execute(
        select(func.count()).select_from(Booking).where(Booking.master_id == master.id)
    )
    bookings = result.scalar()

    # Referrals count
    result = await db.execute(
        select(func.count()).select_from(Referral).where(Referral.referrer_id == master.id)
    )
    referrals = result.scalar()

    # Payments
    result = await db.execute(
        select(func.coalesce(func.sum(Payment.amount_rub), 0))
        .where(Payment.master_id == master.id, Payment.status == "paid")
    )
    paid_total = result.scalar()

    # Last events
    result = await db.execute(
        select(Event)
        .where(Event.master_id == master.id)
        .order_by(Event.created_at.desc())
        .limit(5)
    )
    events = list(result.scalars().all())

    events_text = "\n".join(
        f"  {e.created_at.strftime('%d.%m %H:%M')} — {e.event_type}"
        for e in events
    ) or "  (нет)"

    text = (
        f"👤 <b>Мастер #{master.id}</b>\n\n"
        f"Имя: {master.display_name}\n"
        f"Username: @{master.username}\n"
        f"Telegram ID: {master.telegram_id}\n"
        f"Ниша: {master.niche or '—'}\n"
        f"Онбоардился: {'✅' if master.is_onboarded else '❌'}\n"
        f"Подписка: {master.subscription_status}\n"
        f"Реф.код: {master.referral_code}\n"
        f"Бонус дней: {master.referral_bonus_days}\n\n"
        f"📅 Записей: {bookings}\n"
        f"🎁 Рефералов: {referrals}\n"
        f"💰 Оплатил: {paid_total} ₽\n\n"
        f"<b>Последние события:</b>\n{events_text}"
    )
    await message.answer(text)

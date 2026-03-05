from datetime import datetime, timedelta, timezone

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Master, Payment

router = Router()


@router.message(Command("revenue"))
async def cmd_revenue(message: Message, db: AsyncSession):
    now = datetime.now(timezone.utc)
    month_ago = now - timedelta(days=30)

    # Paying masters
    result = await db.execute(
        select(func.count()).select_from(Master)
        .where(Master.subscription_status == "active")
    )
    paying = result.scalar()
    mrr = paying * 199

    # Total revenue this month
    result = await db.execute(
        select(func.coalesce(func.sum(Payment.amount_rub), 0))
        .where(Payment.created_at >= month_ago, Payment.status == "paid")
    )
    revenue_month = result.scalar()

    # Total revenue all time
    result = await db.execute(
        select(func.coalesce(func.sum(Payment.amount_rub), 0))
        .where(Payment.status == "paid")
    )
    revenue_total = result.scalar()

    # Total masters for conversion
    result = await db.execute(
        select(func.count()).select_from(Master).where(Master.is_onboarded == True)
    )
    onboarded = result.scalar() or 1
    conversion = (paying / onboarded * 100) if onboarded else 0

    text = (
        f"💰 <b>Выручка</b>\n\n"
        f"MRR: <b>{mrr:,} ₽</b>\n"
        f"Платящих мастеров: <b>{paying}</b>\n"
        f"trial→paid конверсия: <b>{conversion:.1f}%</b>\n\n"
        f"Выручка за 30 дней: <b>{revenue_month:,} ₽</b>\n"
        f"Выручка всего: <b>{revenue_total:,} ₽</b>"
    )
    await message.answer(text)

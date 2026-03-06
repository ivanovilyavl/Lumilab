from datetime import datetime, timedelta

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Master, Booking, Event

router = Router()


@router.message(Command("users"))
async def cmd_users(message: Message, db: AsyncSession):
    now = datetime.utcnow()
    month_ago = now - timedelta(days=30)

    # Total
    result = await db.execute(select(func.count()).select_from(Master))
    total = result.scalar()

    # Onboarded
    result = await db.execute(
        select(func.count()).select_from(Master).where(Master.is_onboarded == True)
    )
    onboarded = result.scalar()

    # Active (at least 1 booking this month)
    result = await db.execute(
        select(func.count(func.distinct(Booking.master_id)))
        .where(Booking.created_at >= month_ago)
    )
    active = result.scalar()

    # Churned (onboarded but no events in 30 days)
    result = await db.execute(
        select(func.count()).select_from(Master)
        .where(
            Master.is_onboarded == True,
            Master.subscription_status == "expired",
        )
    )
    churned = result.scalar()

    text = (
        f"👤 <b>Пользователи</b>\n\n"
        f"Всего: <b>{total}</b>\n"
        f"Онбоардились: <b>{onboarded}</b>\n"
        f"Активных (≥1 запись/мес): <b>{active}</b>\n"
        f"Churned (expired): <b>{churned}</b>"
    )
    await message.answer(text)

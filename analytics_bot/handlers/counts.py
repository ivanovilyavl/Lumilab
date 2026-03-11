from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Booking, Master

router = Router()


@router.message(Command("counts"))
async def cmd_counts(message: Message, db: AsyncSession):
    # Total masters registered
    result = await db.execute(select(func.count()).select_from(Master))
    total_masters = result.scalar() or 0

    # Onboarded masters
    result = await db.execute(
        select(func.count()).select_from(Master).where(Master.is_onboarded == True)
    )
    onboarded_masters = result.scalar() or 0

    # Unique clients — distinct non-null client_tg_hash across all bookings
    result = await db.execute(
        select(func.count(func.distinct(Booking.client_tg_hash)))
        .where(Booking.client_tg_hash.isnot(None))
    )
    unique_clients = result.scalar() or 0

    # Total bookings
    result = await db.execute(select(func.count()).select_from(Booking))
    total_bookings = result.scalar() or 0

    await message.answer(
        f"📊 <b>Счётчики</b>\n\n"
        f"👤 Мастеров зарегистрировано: <b>{total_masters}</b>\n"
        f"✅ Завершили онбординг: <b>{onboarded_masters}</b>\n"
        f"👥 Уникальных клиентов: <b>{unique_clients}</b>\n"
        f"📅 Всего записей: <b>{total_bookings}</b>"
    )

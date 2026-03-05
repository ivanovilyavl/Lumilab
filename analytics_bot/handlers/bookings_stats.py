from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Booking

router = Router()


@router.message(Command("bookings"))
async def cmd_bookings_stats(message: Message, db: AsyncSession):
    result = await db.execute(select(func.count()).select_from(Booking))
    total = result.scalar() or 0

    result = await db.execute(
        select(func.count()).select_from(Booking).where(Booking.status == "confirmed")
    )
    confirmed = result.scalar() or 0

    result = await db.execute(
        select(func.count()).select_from(Booking).where(Booking.status == "no_show")
    )
    no_show = result.scalar() or 0

    result = await db.execute(
        select(func.count()).select_from(Booking).where(Booking.status == "cancelled")
    )
    cancelled = result.scalar() or 0

    conf_rate = (confirmed / total * 100) if total else 0
    noshow_rate = (no_show / total * 100) if total else 0

    text = (
        f"📅 <b>Записи</b>\n\n"
        f"Всего: <b>{total}</b>\n"
        f"Confirmed: <b>{confirmed}</b> ({conf_rate:.1f}%)\n"
        f"Cancelled: <b>{cancelled}</b>\n"
        f"No-show: <b>{no_show}</b> ({noshow_rate:.1f}%)"
    )
    await message.answer(text)

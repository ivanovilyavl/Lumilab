from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import func, select, exists
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Master, Service, ScheduleTemplate, Booking, Event

router = Router()


def bar(pct: float, width: int = 16) -> str:
    filled = int(pct / 100 * width)
    return "█" * filled + "░" * (width - filled)


@router.message(Command("funnel"))
async def cmd_funnel(message: Message, db: AsyncSession):
    # Registered
    result = await db.execute(select(func.count()).select_from(Master))
    registered = result.scalar() or 0

    # Onboarded
    result = await db.execute(
        select(func.count()).select_from(Master).where(Master.is_onboarded == True)
    )
    onboarded = result.scalar() or 0

    # Has services
    result = await db.execute(
        select(func.count(func.distinct(Service.master_id)))
    )
    has_services = result.scalar() or 0

    # Has schedule
    result = await db.execute(
        select(func.count(func.distinct(ScheduleTemplate.master_id)))
        .where(ScheduleTemplate.is_working == True)
    )
    has_schedule = result.scalar() or 0

    # Got first booking
    result = await db.execute(
        select(func.count(func.distinct(Booking.master_id)))
    )
    has_booking = result.scalar() or 0

    # Paying
    result = await db.execute(
        select(func.count()).select_from(Master)
        .where(Master.subscription_status == "active")
    )
    paying = result.scalar() or 0

    base = registered or 1

    steps = [
        ("Зарегистрировались", registered),
        ("Завершили онбординг", onboarded),
        ("Добавили ≥1 услугу", has_services),
        ("Настроили расписание", has_schedule),
        ("Получили первую запись", has_booking),
        ("Оформили подписку", paying),
    ]

    lines = ["═══ ВОРОНКА АКТИВАЦИИ ═══"]
    for label, count in steps:
        pct = count / base * 100
        lines.append(f"{label:<26}{count:>5}  {bar(pct)}  {pct:>4.0f}%")

    await message.answer(f"<pre>{chr(10).join(lines)}</pre>")

from datetime import datetime, timedelta

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Master, Booking, Event, Payment

router = Router()


@router.message(Command("stats"))
async def cmd_stats(message: Message, db: AsyncSession):
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)

    # Today stats
    new_masters_today = await _count_events(db, "master_registered", today_start)
    onboarded_today = await _count_events(db, "master_onboarded", today_start)
    bookings_created_today = await _count_events(db, "booking_created", today_start)
    bookings_confirmed_today = await _count_events(db, "booking_confirmed", today_start)
    new_subs_today = await _count_events(db, "subscription_activated", today_start)

    # Today revenue
    result = await db.execute(
        select(func.coalesce(func.sum(Payment.amount_rub), 0))
        .where(Payment.created_at >= today_start, Payment.status == "paid")
    )
    revenue_today = result.scalar()

    # Week stats
    new_masters_week = await _count_events(db, "master_registered", week_ago)

    # Active masters this week (had any event)
    result = await db.execute(
        select(func.count(func.distinct(Event.master_id)))
        .where(Event.created_at >= week_ago, Event.master_id.isnot(None))
    )
    active_week = result.scalar()

    # MRR estimate
    result = await db.execute(
        select(func.count()).select_from(Master)
        .where(Master.subscription_status == "active")
    )
    paying_count = result.scalar()
    mrr = paying_count * 199

    # Trial to paid conversion
    result = await db.execute(select(func.count()).select_from(Master))
    total_masters = result.scalar() or 1
    conversion = (paying_count / total_masters * 100) if total_masters else 0

    # Totals
    result = await db.execute(
        select(func.count()).select_from(Master).where(Master.is_onboarded == True)
    )
    onboarded_total = result.scalar()
    onboarded_pct = (onboarded_total / total_masters * 100) if total_masters else 0
    paying_pct = (paying_count / onboarded_total * 100) if onboarded_total else 0

    result = await db.execute(select(func.count()).select_from(Booking))
    total_bookings = result.scalar()

    text = (
        f"═══ СВОДКА: сегодня ═══\n"
        f"👤 Новых мастеров:        +{new_masters_today}\n"
        f"✅ Завершили онбординг:   +{onboarded_today}\n"
        f"📅 Записей создано:       +{bookings_created_today}\n"
        f"✅ Записей подтверждено:  +{bookings_confirmed_today}\n"
        f"💰 Новых подписок:        +{new_subs_today}\n"
        f"💸 Выручка:               {revenue_today} ₽\n"
        f"\n═══ За 7 дней ═══\n"
        f"👤 Новых мастеров:        +{new_masters_week}\n"
        f"📅 Активных мастеров:     {active_week}\n"
        f"💰 MRR (оценка):          {mrr:,} ₽\n"
        f"📊 trial→paid конверсия:  {conversion:.1f}%\n"
        f"\n═══ Всего ═══\n"
        f"👤 Мастеров зарег.:       {total_masters}\n"
        f"✅ Onboarded:              {onboarded_total}  ({onboarded_pct:.1f}%)\n"
        f"💳 Платящих:              {paying_count}  ({paying_pct:.1f}%)\n"
        f"📅 Записей в системе:     {total_bookings}"
    )

    await message.answer(f"<pre>{text}</pre>")


async def _count_events(db: AsyncSession, event_type: str, since: datetime) -> int:
    result = await db.execute(
        select(func.count()).select_from(Event)
        .where(Event.event_type == event_type, Event.created_at >= since)
    )
    return result.scalar() or 0

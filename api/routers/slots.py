from datetime import date, time, timedelta, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db
from db.models import Booking, ScheduleOverride, ScheduleTemplate

router = APIRouter(prefix="/api", tags=["slots"])


class SlotOut(BaseModel):
    start_time: str  # HH:MM
    end_time: str    # HH:MM


def time_to_minutes(t: time) -> int:
    return t.hour * 60 + t.minute


def minutes_to_time(m: int) -> time:
    return time(m // 60, m % 60)


def generate_slots(start: time, end: time, step_min: int, service_duration: int) -> list[tuple[time, time]]:
    """Generate all theoretical time slots."""
    slots = []
    current = time_to_minutes(start)
    end_min = time_to_minutes(end)
    while current + service_duration <= end_min:
        slot_start = minutes_to_time(current)
        slot_end = minutes_to_time(current + service_duration)
        slots.append((slot_start, slot_end))
        current += step_min
    return slots


def overlaps(slot_start: time, slot_end: time, booked: list[Booking]) -> bool:
    """Check if a slot overlaps with any booked appointment."""
    for b in booked:
        if slot_start < b.end_time and slot_end > b.start_time:
            return True
    return False


@router.get("/master/{master_id}/slots", response_model=list[SlotOut])
async def get_available_slots(
    master_id: int,
    date_str: str = Query(..., alias="date", pattern=r"^\d{4}-\d{2}-\d{2}$"),
    service_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
):
    # Parse date
    try:
        target_date = date.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(400, "Invalid date format. Use YYYY-MM-DD")

    # Don't allow booking in the past
    if target_date < date.today():
        return []

    # Get service duration
    from db.models import Service
    service = await db.get(Service, service_id)
    if not service or service.master_id != master_id:
        raise HTTPException(404, "Service not found")

    day_of_week = target_date.weekday()  # 0=Mon

    # 1. Get template for this day
    result = await db.execute(
        select(ScheduleTemplate).where(
            ScheduleTemplate.master_id == master_id,
            ScheduleTemplate.day_of_week == day_of_week,
            ScheduleTemplate.is_working == True,
        )
    )
    template = result.scalar_one_or_none()

    if not template:
        return []  # Day off by template

    # 2. Check override
    result = await db.execute(
        select(ScheduleOverride).where(
            ScheduleOverride.master_id == master_id,
            ScheduleOverride.date == target_date,
        )
    )
    override = result.scalar_one_or_none()

    if override and not override.is_working:
        return []  # Day off by override

    working_from = override.start_time if override and override.start_time else template.start_time
    working_to = override.end_time if override and override.end_time else template.end_time
    step = template.slot_step_min

    # 3. Generate all theoretical slots
    all_slots = generate_slots(working_from, working_to, step, service.duration_min)

    # 4. Exclude booked slots (confirmed + pending)
    result = await db.execute(
        select(Booking).where(
            Booking.master_id == master_id,
            Booking.booking_date == target_date,
            Booking.status.in_(["confirmed", "pending"]),
        )
    )
    booked = list(result.scalars().all())

    available = [
        SlotOut(
            start_time=s[0].strftime("%H:%M"),
            end_time=s[1].strftime("%H:%M"),
        )
        for s in all_slots
        if not overlaps(s[0], s[1], booked)
    ]

    return available

from datetime import date, time

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db
from db.models import Booking, Event, Master, Service

router = APIRouter(prefix="/api", tags=["bookings"])


class BookingCreate(BaseModel):
    master_id: int
    service_id: int
    date: str           # YYYY-MM-DD
    start_time: str     # HH:MM
    client_name: str
    client_phone: str | None = None
    client_telegram_id: int | None = None


class BookingOut(BaseModel):
    id: int
    status: str
    master_name: str
    service_name: str
    date: str
    start_time: str
    end_time: str


@router.post("/bookings", response_model=BookingOut)
async def create_booking(data: BookingCreate, db: AsyncSession = Depends(get_db)):
    # Validate master
    master = await db.get(Master, data.master_id)
    if not master or not master.is_active:
        raise HTTPException(404, "Master not found")

    # Validate service
    service = await db.get(Service, data.service_id)
    if not service or service.master_id != data.master_id or not service.is_active:
        raise HTTPException(404, "Service not found")

    # Parse date/time
    try:
        booking_date = date.fromisoformat(data.date)
        parts = data.start_time.split(":")
        start_time = time(int(parts[0]), int(parts[1]))
    except (ValueError, IndexError):
        raise HTTPException(400, "Invalid date or time format")

    # Calculate end time
    total_min = start_time.hour * 60 + start_time.minute + service.duration_min
    end_time = time(total_min // 60, total_min % 60)

    # Check for double booking
    result = await db.execute(
        select(Booking).where(
            Booking.master_id == data.master_id,
            Booking.booking_date == booking_date,
            Booking.status.in_(["confirmed", "pending"]),
            Booking.start_time < end_time,
            Booking.end_time > start_time,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(409, "This time slot is already booked")

    booking = Booking(
        master_id=data.master_id,
        service_id=data.service_id,
        client_name=data.client_name,
        client_phone=data.client_phone,
        client_telegram_id=data.client_telegram_id,
        booking_date=booking_date,
        start_time=start_time,
        end_time=end_time,
        status="pending",
        source="miniapp",
    )
    db.add(booking)

    # Log event
    db.add(Event(
        master_id=data.master_id,
        event_type="booking_created",
        payload={"client_name": data.client_name, "service_id": data.service_id},
    ))

    await db.commit()
    await db.refresh(booking)

    return BookingOut(
        id=booking.id,
        status=booking.status,
        master_name=master.display_name,
        service_name=service.name,
        date=str(booking.booking_date),
        start_time=booking.start_time.strftime("%H:%M"),
        end_time=booking.end_time.strftime("%H:%M"),
    )


@router.get("/bookings/{booking_id}")
async def get_booking(booking_id: int, db: AsyncSession = Depends(get_db)):
    booking = await db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(404, "Booking not found")

    master = await db.get(Master, booking.master_id)
    service = await db.get(Service, booking.service_id)

    return BookingOut(
        id=booking.id,
        status=booking.status,
        master_name=master.display_name if master else "—",
        service_name=service.name if service else "—",
        date=str(booking.booking_date),
        start_time=booking.start_time.strftime("%H:%M"),
        end_time=booking.end_time.strftime("%H:%M"),
    )

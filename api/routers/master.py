from datetime import date, time, timedelta

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db, get_master_owner
from db.models import Booking, Master, QAItem, Service

router = APIRouter(prefix="/api", tags=["master"])

MAX_RECURRING_INSTANCES = 52


class ServiceOut(BaseModel):
    id: int
    name: str
    description: str | None
    price: int | None
    duration_min: int

    model_config = {"from_attributes": True}


class QAItemOut(BaseModel):
    id: int
    question: str
    answer: str

    model_config = {"from_attributes": True}


class MasterOut(BaseModel):
    id: int
    username: str
    display_name: str | None
    bio: str | None
    photo_file_id: str | None
    niche: str | None
    language: str
    currency: str
    accepting_bookings: bool
    services: list[ServiceOut]
    qa_items: list[QAItemOut]

    model_config = {"from_attributes": True}


class MasterBookingItem(BaseModel):
    id: int
    date: str
    start_time: str
    end_time: str
    status: str
    service_name: str
    client_pseudo: str
    client_notes: str | None


class MasterScheduleOut(BaseModel):
    bookings: list[MasterBookingItem]


class MasterBookingCreate(BaseModel):
    service_id: int
    date: str           # YYYY-MM-DD
    start_time: str     # HH:MM
    client_name: str
    client_phone: str | None = None
    client_tg_username: str | None = None
    is_recurring: bool = False
    recurrence_end_date: str | None = None  # YYYY-MM-DD


class MasterBookingCreateResult(BaseModel):
    created: int
    booking_ids: list[int]



@router.get("/master/{username}/schedule", response_model=MasterScheduleOut)
async def get_master_schedule(
    username: str,
    db: AsyncSession = Depends(get_db),
    x_telegram_init_data: str | None = Header(default=None),
):
    master = await get_master_owner(username, x_telegram_init_data, db)

    today = date.today()
    rows = await db.execute(
        select(Booking, Service)
        .join(Service, Booking.service_id == Service.id)
        .where(
            Booking.master_id == master.id,
            Booking.booking_date >= today,
            Booking.status.in_(["confirmed", "pending"]),
        )
        .order_by(Booking.booking_date, Booking.start_time)
    )
    bookings = [
        MasterBookingItem(
            id=b.id,
            date=str(b.booking_date),
            start_time=b.start_time.strftime("%H:%M"),
            end_time=b.end_time.strftime("%H:%M"),
            status=b.status,
            service_name=s.name,
            client_pseudo=b.client_pseudo,
            client_notes=b.client_notes,
        )
        for b, s in rows.all()
    ]
    return MasterScheduleOut(bookings=bookings)


@router.post("/master/{username}/bookings", response_model=MasterBookingCreateResult)
async def create_master_booking(
    username: str,
    data: MasterBookingCreate,
    db: AsyncSession = Depends(get_db),
    x_telegram_init_data: str | None = Header(default=None),
):
    master = await get_master_owner(username, x_telegram_init_data, db)

    # Validate service belongs to this master
    svc_result = await db.execute(
        select(Service).where(
            Service.id == data.service_id,
            Service.master_id == master.id,
            Service.is_active == True,
        )
    )
    service = svc_result.scalar_one_or_none()
    if not service:
        raise HTTPException(404, "Service not found")

    # Parse date / time
    try:
        first_date = date.fromisoformat(data.date)
        h, m = data.start_time.split(":")
        start_t = time(int(h), int(m))
    except (ValueError, IndexError):
        raise HTTPException(400, "Invalid date or time format")

    total_min = start_t.hour * 60 + start_t.minute + service.duration_min
    end_t = time(total_min // 60, total_min % 60)

    # Build list of dates
    dates_to_create: list[date] = [first_date]
    if data.is_recurring:
        if not data.recurrence_end_date:
            raise HTTPException(400, "recurrence_end_date required when is_recurring=true")
        try:
            end_date = date.fromisoformat(data.recurrence_end_date)
        except ValueError:
            raise HTTPException(400, "Invalid recurrence_end_date format")
        if end_date <= first_date:
            raise HTTPException(400, "recurrence_end_date must be after start date")
        cur = first_date + timedelta(weeks=1)
        while cur <= end_date:
            dates_to_create.append(cur)
            cur += timedelta(weeks=1)
        if len(dates_to_create) > MAX_RECURRING_INSTANCES:
            raise HTTPException(400, f"Максимум {MAX_RECURRING_INSTANCES} повторений (около 1 года)")

    client_pseudo = data.client_name.strip()
    notes_parts = []
    if data.client_tg_username:
        tg = data.client_tg_username.strip().lstrip('@')
        if tg:
            notes_parts.append(f"@{tg}")
    if data.client_phone and data.client_phone.strip():
        notes_parts.append(data.client_phone.strip())
    client_notes = " · ".join(notes_parts) if notes_parts else None
    recurrence_end = date.fromisoformat(data.recurrence_end_date) if data.is_recurring and data.recurrence_end_date else None

    created_ids: list[int] = []
    for booking_date_val in dates_to_create:
        # Skip conflicting slots (don't fail the whole batch)
        conflict = await db.execute(
            select(Booking)
            .where(
                Booking.master_id == master.id,
                Booking.booking_date == booking_date_val,
                Booking.status.in_(["confirmed", "pending"]),
                Booking.start_time < end_t,
                Booking.end_time > start_t,
            )
            .with_for_update()
        )
        if conflict.scalar_one_or_none():
            continue

        booking = Booking(
            master_id=master.id,
            service_id=service.id,
            client_pseudo=client_pseudo,
            client_notes=client_notes,
            booking_date=booking_date_val,
            start_time=start_t,
            end_time=end_t,
            status="confirmed",
            source="master_manual",
            is_recurring=data.is_recurring,
            recurrence_end_date=recurrence_end,
        )
        db.add(booking)
        await db.flush()
        created_ids.append(booking.id)

    await db.commit()
    return MasterBookingCreateResult(created=len(created_ids), booking_ids=created_ids)


@router.get("/master/{username}", response_model=MasterOut)
async def get_master(username: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Master).where(Master.username == username, Master.is_active == True)
    )
    master = result.scalar_one_or_none()
    if not master:
        raise HTTPException(status_code=404, detail="Master not found")

    result = await db.execute(
        select(Service).where(
            Service.master_id == master.id,
            Service.is_active == True,
        ).order_by(Service.sort_order)
    )
    services = list(result.scalars().all())

    qa_result = await db.execute(
        select(QAItem).where(
            QAItem.master_id == master.id,
            QAItem.is_active == True,
        ).order_by(QAItem.sort_order)
    )
    qa_items = list(qa_result.scalars().all())

    return MasterOut(
        id=master.id,
        username=master.username,
        display_name=master.display_name,
        bio=master.bio,
        photo_file_id=master.photo_file_id,
        niche=master.niche,
        language=master.language or "ru",
        currency=master.currency or "RUB",
        accepting_bookings=True,
        services=[ServiceOut.model_validate(s) for s in services],
        qa_items=[QAItemOut.model_validate(q) for q in qa_items],
    )

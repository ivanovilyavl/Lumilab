import json
from datetime import date
from urllib.parse import unquote

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import validate_telegram_init_data
from api.deps import get_db
from db.models import Booking, Master, Service

router = APIRouter(prefix="/api", tags=["master"])


class ServiceOut(BaseModel):
    id: int
    name: str
    description: str | None
    price: int
    duration_min: int

    model_config = {"from_attributes": True}


class MasterOut(BaseModel):
    id: int
    username: str
    display_name: str | None
    bio: str | None
    photo_file_id: str | None
    niche: str | None
    accepting_bookings: bool
    services: list[ServiceOut]

    model_config = {"from_attributes": True}


class MasterBookingItem(BaseModel):
    id: int
    date: str
    start_time: str
    end_time: str
    status: str
    service_name: str
    client_pseudo: str


class MasterScheduleOut(BaseModel):
    bookings: list[MasterBookingItem]


@router.get("/master/{username}/schedule", response_model=MasterScheduleOut)
async def get_master_schedule(
    username: str,
    db: AsyncSession = Depends(get_db),
    x_telegram_init_data: str | None = Header(default=None),
):
    if not x_telegram_init_data:
        raise HTTPException(401, "Auth required")

    data = validate_telegram_init_data(x_telegram_init_data)
    if not data:
        raise HTTPException(401, "Invalid auth")

    user_str = data.get("user")
    if not user_str:
        raise HTTPException(401, "No user in auth data")
    try:
        user = json.loads(unquote(user_str))
        telegram_id = int(user["id"])
    except (ValueError, KeyError):
        raise HTTPException(401, "Invalid user data")

    result = await db.execute(
        select(Master).where(Master.username == username, Master.is_active == True)
    )
    master = result.scalar_one_or_none()
    if not master:
        raise HTTPException(404, "Master not found")
    if master.telegram_id != telegram_id:
        raise HTTPException(403, "Forbidden")

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
        )
        for b, s in rows.all()
    ]
    return MasterScheduleOut(bookings=bookings)


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

    return MasterOut(
        id=master.id,
        username=master.username,
        display_name=master.display_name,
        bio=master.bio,
        photo_file_id=master.photo_file_id,
        niche=master.niche,
        accepting_bookings=master.subscription_status != "expired",
        services=[ServiceOut.model_validate(s) for s in services],
    )

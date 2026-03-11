from datetime import date, datetime, time

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db
from db.models import Booking, Event, Master, Service
from shared.config import settings
from shared.i18n import t
from shared.pseudo import hash_client_id, get_or_create_pseudo, generate_pseudo

router = APIRouter(prefix="/api", tags=["bookings"])


class BookingCreate(BaseModel):
    master_id: int
    service_id: int
    date: str           # YYYY-MM-DD
    start_time: str     # HH:MM
    client_telegram_id: int | None = None  # Used only for hashing, not stored


class BookingOut(BaseModel):
    id: int
    status: str
    master_name: str
    service_name: str
    date: str
    start_time: str
    end_time: str
    client_pseudo: str


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

    # Check for double booking with row-level locking (SELECT FOR UPDATE)
    result = await db.execute(
        select(Booking)
        .where(
            Booking.master_id == data.master_id,
            Booking.booking_date == booking_date,
            Booking.status.in_(["confirmed", "pending"]),
            Booking.start_time < end_time,
            Booking.end_time > start_time,
        )
        .with_for_update()
    )
    if result.scalar_one_or_none():
        raise HTTPException(409, "Этот слот только что заняли. Выберите другое время")

    # Generate anonymous client data
    client_tg_hash = None
    if data.client_telegram_id:
        client_tg_hash = hash_client_id(data.client_telegram_id, settings.client_id_hash_secret)

        # Store reverse mapping in Redis (tg_hash -> tg_id) for notifications
        try:
            from redis.asyncio import from_url
            redis = from_url(settings.redis_url)
            await redis.set(f"tghash:{client_tg_hash}", str(data.client_telegram_id), ex=90 * 86400)
            await redis.aclose()
        except Exception:
            pass

    # Get or create pseudonym (same client = same pseudo for this master)
    if client_tg_hash:
        client_pseudo = await get_or_create_pseudo(client_tg_hash, data.master_id, db)
    else:
        client_pseudo = generate_pseudo()

    now = datetime.utcnow()
    booking = Booking(
        master_id=data.master_id,
        service_id=data.service_id,
        client_pseudo=client_pseudo,
        client_tg_hash=client_tg_hash,
        booking_date=booking_date,
        start_time=start_time,
        end_time=end_time,
        status="pending",
        source="miniapp",
        client_consent_given=True,
        client_consent_at=now,
    )
    db.add(booking)

    # Log event (no PII in payload)
    db.add(Event(
        master_id=data.master_id,
        event_type="booking_created",
        payload={"service_id": data.service_id, "pseudo": client_pseudo},
    ))

    await db.commit()
    await db.refresh(booking)

    # Notify master and client about new booking
    try:
        from aiogram import Bot
        from aiogram.client.default import DefaultBotProperties
        from aiogram.enums import ParseMode
        from bot.keyboards.common import booking_notification_kb, client_cancel_kb

        bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        lang = getattr(master, "language", "ru") or "ru"
        currency = getattr(master, "currency", "RUB") or "RUB"
        min_unit = t(lang, "min_unit")
        from shared.i18n import fmt_price as _fmt_price
        price_str = _fmt_price(service.price, currency, lang)

        await bot.send_message(
            master.telegram_id,
            t(lang, "new_booking_master",
              pseudo=client_pseudo,
              service=service.name,
              duration=f"{service.duration_min} {min_unit}",
              price=price_str,
              date=booking_date.strftime("%d.%m.%Y"),
              time=start_time.strftime("%H:%M")),
            reply_markup=booking_notification_kb(booking.id),
        )

        if data.client_telegram_id:
            await bot.send_message(
                data.client_telegram_id,
                t(lang, "booking_created_client",
                  master=master.display_name or "Мастер",
                  service=service.name,
                  duration=f"{service.duration_min} {min_unit}",
                  price=price_str,
                  date=booking_date.strftime("%d.%m.%Y"),
                  time=start_time.strftime("%H:%M")),
                reply_markup=client_cancel_kb(booking.id),
            )

        await bot.session.close()
    except Exception:
        pass

    return BookingOut(
        id=booking.id,
        status=booking.status,
        master_name=master.display_name or "Мастер",
        service_name=service.name,
        date=str(booking.booking_date),
        start_time=booking.start_time.strftime("%H:%M"),
        end_time=booking.end_time.strftime("%H:%M"),
        client_pseudo=client_pseudo,
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
        master_name=(master.display_name or "Мастер") if master else "—",
        service_name=service.name if service else "—",
        date=str(booking.booking_date),
        start_time=booking.start_time.strftime("%H:%M"),
        end_time=booking.end_time.strftime("%H:%M"),
        client_pseudo=booking.client_pseudo,
    )

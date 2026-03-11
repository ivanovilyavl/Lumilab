import json
from datetime import date

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import validate_analytics_init_data
from api.deps import get_db
from db.models import Booking, Master, Service
from shared.config import settings

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ── Auth helper ────────────────────────────────────────────────────────────────

def _require_admin(init_data: str | None) -> int:
    if not init_data:
        raise HTTPException(401, "Auth required")
    auth_data = validate_analytics_init_data(init_data)
    if not auth_data:
        raise HTTPException(401, "Invalid auth")
    user_str = auth_data.get("user")
    if not user_str:
        raise HTTPException(401, "No user in auth data")
    try:
        user = json.loads(user_str)
        telegram_id = int(user["id"])
    except (ValueError, KeyError):
        raise HTTPException(401, "Invalid user data")
    if telegram_id not in settings.admin_ids:
        raise HTTPException(403, "Forbidden")
    return telegram_id


# ── Schemas ────────────────────────────────────────────────────────────────────

class MasterItem(BaseModel):
    id: int
    username: str
    display_name: str | None
    niche: str | None
    language: str
    subscription_status: str
    is_active: bool
    is_onboarded: bool
    consent_given: bool
    created_at: str
    total_bookings: int
    total_clients: int


class AdminClientItem(BaseModel):
    tg_hash: str | None
    pseudo: str
    is_manual: bool
    client_consent_given: bool
    total_bookings: int
    masters_count: int
    last_booking_date: str | None
    services: list[str]


class AdminMastersMessageRequest(BaseModel):
    master_ids: list[int]
    text: str


class AdminClientsMessageRequest(BaseModel):
    tg_hashes: list[str]
    text: str


class MessageResult(BaseModel):
    sent: int
    failed: int
    no_contact: int


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("/masters", response_model=list[MasterItem])
async def list_masters(
    db: AsyncSession = Depends(get_db),
    x_telegram_init_data: str | None = Header(default=None),
):
    _require_admin(x_telegram_init_data)

    result = await db.execute(select(Master).order_by(Master.created_at.desc()))
    masters = result.scalars().all()
    if not masters:
        return []

    master_ids = [m.id for m in masters]

    # Bookings count per master
    bcount = await db.execute(
        select(Booking.master_id, func.count(Booking.id).label("cnt"))
        .where(Booking.master_id.in_(master_ids))
        .group_by(Booking.master_id)
    )
    bookings_by_master = {row.master_id: row.cnt for row in bcount.all()}

    # Distinct clients per master (by client_key = tg_hash or "manual:{pseudo}")
    ccount = await db.execute(
        select(
            Booking.master_id,
            func.count(
                func.distinct(
                    func.coalesce(
                        Booking.client_tg_hash,
                        func.concat("manual:", Booking.client_pseudo),
                    )
                )
            ).label("cnt"),
        )
        .where(Booking.master_id.in_(master_ids))
        .group_by(Booking.master_id)
    )
    clients_by_master = {row.master_id: row.cnt for row in ccount.all()}

    return [
        MasterItem(
            id=m.id,
            username=m.username,
            display_name=m.display_name,
            niche=m.niche,
            language=m.language or "ru",
            subscription_status=m.subscription_status,
            is_active=m.is_active,
            is_onboarded=m.is_onboarded,
            consent_given=m.consent_given,
            created_at=m.created_at.strftime("%Y-%m-%d"),
            total_bookings=bookings_by_master.get(m.id, 0),
            total_clients=clients_by_master.get(m.id, 0),
        )
        for m in masters
    ]


@router.get("/clients", response_model=list[AdminClientItem])
async def list_all_clients(
    db: AsyncSession = Depends(get_db),
    x_telegram_init_data: str | None = Header(default=None),
):
    _require_admin(x_telegram_init_data)
    today = date.today()

    rows = await db.execute(
        select(Booking, Service).join(Service, Booking.service_id == Service.id)
    )

    aggregated: dict[str, dict] = {}
    for booking, service in rows.all():
        if booking.client_tg_hash:
            key = booking.client_tg_hash
            is_manual = False
        else:
            key = f"manual:{booking.client_pseudo}"
            is_manual = True

        if key not in aggregated:
            aggregated[key] = {
                "tg_hash": booking.client_tg_hash,
                "pseudo": booking.client_pseudo,
                "is_manual": is_manual,
                "dates": [],
                "services": set(),
                "master_ids": set(),
                "client_consent_given": False,
            }
        aggregated[key]["dates"].append(booking.booking_date)
        aggregated[key]["services"].add(service.name)
        aggregated[key]["master_ids"].add(booking.master_id)
        if booking.client_consent_given:
            aggregated[key]["client_consent_given"] = True

    result: list[AdminClientItem] = []
    for _key, data in aggregated.items():
        all_dates = data["dates"]
        past = [d for d in all_dates if d <= today]
        last_date = max(past) if past else None
        result.append(
            AdminClientItem(
                tg_hash=data["tg_hash"],
                pseudo=data["pseudo"],
                is_manual=data["is_manual"],
                client_consent_given=data["client_consent_given"],
                total_bookings=len(all_dates),
                masters_count=len(data["master_ids"]),
                last_booking_date=str(last_date) if last_date else None,
                services=sorted(data["services"]),
            )
        )

    result.sort(key=lambda c: c.last_booking_date or "0000-00-00", reverse=True)
    return result


@router.post("/masters/message", response_model=MessageResult)
async def send_message_to_masters(
    data: AdminMastersMessageRequest,
    db: AsyncSession = Depends(get_db),
    x_telegram_init_data: str | None = Header(default=None),
):
    _require_admin(x_telegram_init_data)

    text = data.text.strip()
    if not text:
        raise HTTPException(400, "Message text is empty")
    if len(text) > 2000:
        raise HTTPException(400, "Message too long (max 2000 characters)")

    # Only send to masters who gave consent
    result = await db.execute(
        select(Master).where(
            Master.id.in_(data.master_ids),
            Master.consent_given == True,
        )
    )
    masters = result.scalars().all()

    from aiogram import Bot
    from aiogram.client.default import DefaultBotProperties
    from aiogram.enums import ParseMode

    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    sent = failed = no_contact = 0
    try:
        for master in masters:
            try:
                await bot.send_message(
                    master.telegram_id,
                    f"📢 <b>Сообщение от команды Plotina bot:</b>\n\n{text}",
                )
                sent += 1
            except Exception:
                failed += 1
        # Masters in request that had no consent counted as no_contact
        no_contact = len(data.master_ids) - len(masters)
    finally:
        await bot.session.close()

    return MessageResult(sent=sent, failed=failed, no_contact=no_contact)


@router.post("/clients/message", response_model=MessageResult)
async def send_message_to_clients(
    data: AdminClientsMessageRequest,
    x_telegram_init_data: str | None = Header(default=None),
):
    _require_admin(x_telegram_init_data)

    text = data.text.strip()
    if not text:
        raise HTTPException(400, "Message text is empty")
    if len(text) > 2000:
        raise HTTPException(400, "Message too long (max 2000 characters)")

    from aiogram import Bot
    from aiogram.client.default import DefaultBotProperties
    from aiogram.enums import ParseMode
    from redis.asyncio import from_url as redis_from_url

    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    redis = redis_from_url(settings.redis_url)
    sent = failed = no_contact = 0
    try:
        for tg_hash in data.tg_hashes:
            tg_id_bytes = await redis.get(f"tghash:{tg_hash}")
            if not tg_id_bytes:
                failed += 1
                continue
            try:
                await bot.send_message(
                    int(tg_id_bytes),
                    f"📢 <b>Сообщение от команды Plotina bot:</b>\n\n{text}",
                )
                sent += 1
            except Exception:
                failed += 1
    finally:
        await redis.aclose()
        await bot.session.close()

    return MessageResult(sent=sent, failed=failed, no_contact=no_contact)

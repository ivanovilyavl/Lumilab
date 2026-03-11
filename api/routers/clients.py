from datetime import date

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db, get_master_owner
from db.models import Booking, ClientAlias, ClientNote, Service

router = APIRouter(prefix="/api", tags=["clients"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class ClientItem(BaseModel):
    client_key: str          # tg_hash  OR  "manual:{pseudo}"
    tg_hash: str | None
    pseudo: str
    total_bookings: int
    last_booking_date: str | None
    next_booking_date: str | None
    services: list[str]      # unique service names
    note: str | None
    can_message: bool        # True when telegram_id can be resolved via Redis
    is_active: bool          # booking in last 90 days OR upcoming booking


class NoteUpdate(BaseModel):
    note: str | None


class MessageRequest(BaseModel):
    client_keys: list[str]
    text: str


class MessageResult(BaseModel):
    sent: int
    failed: int
    no_contact: int          # manual clients without telegram contact


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_client_key(tg_hash: str | None, pseudo: str) -> str:
    return tg_hash if tg_hash else f"manual:{pseudo}"


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/master/{username}/clients", response_model=list[ClientItem])
async def list_clients(
    username: str,
    db: AsyncSession = Depends(get_db),
    x_telegram_init_data: str | None = Header(default=None),
):
    master = await get_master_owner(username, x_telegram_init_data, db)
    today = date.today()

    # Fetch all bookings with service names
    rows = await db.execute(
        select(Booking, Service)
        .join(Service, Booking.service_id == Service.id)
        .where(Booking.master_id == master.id)
    )

    # Aggregate by client_key
    aggregated: dict[str, dict] = {}
    for booking, service in rows.all():
        key = _build_client_key(booking.client_tg_hash, booking.client_pseudo)
        if key not in aggregated:
            aggregated[key] = {
                "tg_hash": booking.client_tg_hash,
                "pseudo": booking.client_pseudo,
                "dates": [],
                "services": set(),
            }
        aggregated[key]["dates"].append(booking.booking_date)
        aggregated[key]["services"].add(service.name)

    if not aggregated:
        return []

    # Fetch notes for all client_keys
    note_rows = await db.execute(
        select(ClientNote).where(
            ClientNote.master_id == master.id,
            ClientNote.client_key.in_(list(aggregated.keys())),
        )
    )
    notes: dict[str, str | None] = {n.client_key: n.note for n in note_rows.scalars().all()}

    # Build response
    result: list[ClientItem] = []
    for key, data in aggregated.items():
        all_dates = data["dates"]
        past = [d for d in all_dates if d <= today]
        future = [d for d in all_dates if d > today]
        last_date = max(past) if past else None
        next_date = min(future) if future else None
        is_active = bool(next_date) or (last_date is not None and (today - last_date).days <= 90)

        result.append(ClientItem(
            client_key=key,
            tg_hash=data["tg_hash"],
            pseudo=data["pseudo"],
            total_bookings=len(all_dates),
            last_booking_date=str(last_date) if last_date else None,
            next_booking_date=str(next_date) if next_date else None,
            services=sorted(data["services"]),
            note=notes.get(key),
            can_message=bool(data["tg_hash"]),
            is_active=is_active,
        ))

    result.sort(key=lambda c: c.last_booking_date or "0000-00-00", reverse=True)
    return result


@router.patch("/master/{username}/clients/note")
async def update_client_note(
    username: str,
    data: NoteUpdate,
    client_key: str,
    db: AsyncSession = Depends(get_db),
    x_telegram_init_data: str | None = Header(default=None),
):
    master = await get_master_owner(username, x_telegram_init_data, db)

    row = await db.execute(
        select(ClientNote).where(
            ClientNote.master_id == master.id,
            ClientNote.client_key == client_key,
        )
    )
    note_obj = row.scalar_one_or_none()

    if note_obj:
        note_obj.note = data.note
    else:
        db.add(ClientNote(master_id=master.id, client_key=client_key, note=data.note))

    await db.commit()
    return {"ok": True}


@router.post("/master/{username}/clients/message", response_model=MessageResult)
async def send_message_to_clients(
    username: str,
    data: MessageRequest,
    db: AsyncSession = Depends(get_db),
    x_telegram_init_data: str | None = Header(default=None),
):
    master = await get_master_owner(username, x_telegram_init_data, db)

    text = data.text.strip()
    if not text:
        raise HTTPException(400, "Message text is empty")
    if len(text) > 2000:
        raise HTTPException(400, "Message too long (max 2000 characters)")

    from aiogram import Bot
    from aiogram.client.default import DefaultBotProperties
    from aiogram.enums import ParseMode
    from redis.asyncio import from_url as redis_from_url
    from shared.config import settings

    redis = redis_from_url(settings.redis_url)
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    sent = failed = no_contact = 0
    try:
        for key in data.client_keys:
            # Manual bookings have no telegram contact
            if key.startswith("manual:"):
                no_contact += 1
                continue

            tg_id_bytes = await redis.get(f"tghash:{key}")
            if not tg_id_bytes:
                failed += 1
                continue

            try:
                await bot.send_message(
                    int(tg_id_bytes),
                    f"💬 Сообщение от мастера <b>{master.display_name or master.username}</b>:\n\n{text}",
                )
                sent += 1
            except Exception:
                failed += 1
    finally:
        await redis.aclose()
        await bot.session.close()

    return MessageResult(sent=sent, failed=failed, no_contact=no_contact)

import csv
import io
from datetime import datetime, timedelta

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, BufferedInputFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Master, Booking

router = Router()


@router.message(Command("export"))
async def cmd_export(message: Message, db: AsyncSession, command: CommandObject):
    args = (command.args or "masters").strip().lower()

    if args.startswith("masters"):
        await _export_masters(message, db)
    elif args.startswith("bookings"):
        await _export_bookings(message, db)
    else:
        await message.answer("Использование: /export masters или /export bookings")


async def _export_masters(message: Message, db: AsyncSession):
    result = await db.execute(select(Master).order_by(Master.created_at.desc()))
    masters = list(result.scalars().all())

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "telegram_id", "username", "display_name", "niche",
                      "subscription_status", "is_onboarded", "created_at"])
    for m in masters:
        writer.writerow([m.id, m.telegram_id, m.username, m.display_name, m.niche,
                         m.subscription_status, m.is_onboarded, m.created_at])

    data = buf.getvalue().encode("utf-8-sig")
    doc = BufferedInputFile(data, filename="masters_export.csv")
    await message.answer_document(doc, caption=f"Экспорт мастеров: {len(masters)} записей")


async def _export_bookings(message: Message, db: AsyncSession):
    month_ago = datetime.utcnow() - timedelta(days=30)
    result = await db.execute(
        select(Booking)
        .where(Booking.created_at >= month_ago)
        .order_by(Booking.created_at.desc())
    )
    bookings = list(result.scalars().all())

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "master_id", "service_id", "client_name",
                      "booking_date", "start_time", "status", "source", "created_at"])
    for b in bookings:
        writer.writerow([b.id, b.master_id, b.service_id, b.client_name,
                         b.booking_date, b.start_time, b.status, b.source, b.created_at])

    data = buf.getvalue().encode("utf-8-sig")
    doc = BufferedInputFile(data, filename="bookings_export.csv")
    await message.answer_document(doc, caption=f"Экспорт записей (30 дней): {len(bookings)}")

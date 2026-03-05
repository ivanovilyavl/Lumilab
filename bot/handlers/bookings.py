from datetime import date, datetime, timezone

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.keyboards.common import booking_tabs_kb
from db.models import Master, Booking, Service, Event

router = Router()


def format_booking(b: Booking) -> str:
    status_map = {
        "pending": "⏳",
        "confirmed": "✅",
        "cancelled": "❌",
        "completed": "✔️",
        "no_show": "🚫",
    }
    icon = status_map.get(b.status, "❓")
    svc_name = b.service.name if b.service else "—"
    return (
        f"{icon} <b>{b.client_name}</b>\n"
        f"   {svc_name} · {b.booking_date.strftime('%d.%m')} в {b.start_time.strftime('%H:%M')}\n"
    )


@router.message(Command("bookings"))
@router.message(F.text == "📖 Записи")
async def cmd_bookings(message: Message, db: AsyncSession, master: Master):
    # Show pending by default
    result = await db.execute(
        select(Booking)
        .options(selectinload(Booking.service))
        .where(Booking.master_id == master.id, Booking.status == "pending")
        .order_by(Booking.booking_date, Booking.start_time)
    )
    bookings = list(result.scalars().all())

    if not bookings:
        text = "📖 <b>Записи</b>\n\n⏳ Ожидающих подтверждения записей нет."
    else:
        lines = [format_booking(b) for b in bookings]
        text = f"📖 <b>Ожидают подтверждения ({len(bookings)}):</b>\n\n" + "\n".join(lines)

    # Add action buttons for pending bookings
    buttons = []
    for b in bookings[:10]:
        buttons.append([
            InlineKeyboardButton(text=f"✅ {b.client_name}", callback_data=f"bk_confirm:{b.id}"),
            InlineKeyboardButton(text=f"❌", callback_data=f"bk_reject:{b.id}"),
        ])

    tabs = [
        [
            InlineKeyboardButton(text="⏳ Ожидают", callback_data="tab:pending"),
            InlineKeyboardButton(text="📅 Предстоящие", callback_data="tab:upcoming"),
            InlineKeyboardButton(text="📋 История", callback_data="tab:history"),
        ]
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons + tabs)
    await message.answer(text, reply_markup=kb)


@router.callback_query(F.data == "tab:pending")
async def tab_pending(callback: CallbackQuery, db: AsyncSession, master: Master):
    result = await db.execute(
        select(Booking)
        .options(selectinload(Booking.service))
        .where(Booking.master_id == master.id, Booking.status == "pending")
        .order_by(Booking.booking_date, Booking.start_time)
    )
    bookings = list(result.scalars().all())
    if not bookings:
        text = "⏳ Нет ожидающих записей."
    else:
        lines = [format_booking(b) for b in bookings]
        text = f"⏳ <b>Ожидают ({len(bookings)}):</b>\n\n" + "\n".join(lines)
    await callback.message.edit_text(text, reply_markup=booking_tabs_kb())
    await callback.answer()


@router.callback_query(F.data == "tab:upcoming")
async def tab_upcoming(callback: CallbackQuery, db: AsyncSession, master: Master):
    today = date.today()
    result = await db.execute(
        select(Booking)
        .options(selectinload(Booking.service))
        .where(
            Booking.master_id == master.id,
            Booking.status == "confirmed",
            Booking.booking_date >= today,
        )
        .order_by(Booking.booking_date, Booking.start_time)
        .limit(20)
    )
    bookings = list(result.scalars().all())
    if not bookings:
        text = "📅 Нет предстоящих записей."
    else:
        lines = [format_booking(b) for b in bookings]
        text = f"📅 <b>Предстоящие ({len(bookings)}):</b>\n\n" + "\n".join(lines)
    await callback.message.edit_text(text, reply_markup=booking_tabs_kb())
    await callback.answer()


@router.callback_query(F.data == "tab:history")
async def tab_history(callback: CallbackQuery, db: AsyncSession, master: Master):
    result = await db.execute(
        select(Booking)
        .options(selectinload(Booking.service))
        .where(
            Booking.master_id == master.id,
            Booking.status.in_(["completed", "cancelled", "no_show"]),
        )
        .order_by(Booking.booking_date.desc())
        .limit(20)
    )
    bookings = list(result.scalars().all())
    if not bookings:
        text = "📋 История пуста."
    else:
        lines = [format_booking(b) for b in bookings]
        text = f"📋 <b>История:</b>\n\n" + "\n".join(lines)
    await callback.message.edit_text(text, reply_markup=booking_tabs_kb())
    await callback.answer()


@router.callback_query(F.data.startswith("bk_confirm:"))
async def bk_confirm(callback: CallbackQuery, db: AsyncSession, master: Master):
    booking_id = int(callback.data.split(":")[1])
    booking = await db.get(Booking, booking_id)
    if not booking or booking.master_id != master.id:
        await callback.answer("Запись не найдена", show_alert=True)
        return
    booking.status = "confirmed"
    db.add(Event(master_id=master.id, event_type="booking_confirmed", payload={"booking_id": booking.id}))
    await db.commit()
    await callback.answer("✅ Запись подтверждена!")

    # Notify client if they have telegram_id
    if booking.client_telegram_id:
        try:
            bot = callback.bot
            await bot.send_message(
                booking.client_telegram_id,
                f"✅ Ваша запись подтверждена!\n\n"
                f"👤 {master.display_name}\n"
                f"📅 {booking.booking_date.strftime('%d.%m.%Y')} в {booking.start_time.strftime('%H:%M')}",
            )
        except Exception:
            pass

    await callback.message.edit_text(
        f"✅ Запись <b>{booking.client_name}</b> подтверждена!",
        reply_markup=booking_tabs_kb(),
    )


@router.callback_query(F.data.startswith("bk_reject:"))
async def bk_reject(callback: CallbackQuery, db: AsyncSession, master: Master):
    booking_id = int(callback.data.split(":")[1])
    booking = await db.get(Booking, booking_id)
    if not booking or booking.master_id != master.id:
        await callback.answer("Запись не найдена", show_alert=True)
        return
    booking.status = "cancelled"
    db.add(Event(master_id=master.id, event_type="booking_cancelled", payload={"booking_id": booking.id}))
    await db.commit()
    await callback.answer("❌ Запись отклонена")

    if booking.client_telegram_id:
        try:
            bot = callback.bot
            await bot.send_message(
                booking.client_telegram_id,
                f"😔 К сожалению, мастер {master.display_name} не смог принять вашу запись "
                f"на {booking.booking_date.strftime('%d.%m.%Y')} в {booking.start_time.strftime('%H:%M')}.",
            )
        except Exception:
            pass

    await callback.message.edit_text(
        f"❌ Запись <b>{booking.client_name}</b> отклонена.",
        reply_markup=booking_tabs_kb(),
    )

import logging
from datetime import date, timedelta

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.handlers.services import fmt_price
from shared.i18n import t
from bot.keyboards.common import (
    booking_tabs_kb,
    client_cancel_confirm_kb,
    client_reply_kb,
)
from bot.states.onboarding import (
    MasterMessageStates,
    MasterRejectReasonStates,
    MasterCancelReasonStates,
    ClientReplyStates,
)
from db.models import Master, Booking, Service, Event, BotMessage

logger = logging.getLogger(__name__)
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
    price = f" · {b.service.price} ₽" if b.service and b.service.price else ""
    duration = f" · {b.service.duration_min} мин" if b.service else ""
    return (
        f"{icon} <b>{b.client_pseudo}</b>\n"
        f"   {svc_name}{duration}{price}\n"
        f"   {b.booking_date.strftime('%d.%m')} в {b.start_time.strftime('%H:%M')}\n"
    )


# ── Вкладка: Ожидают ──────────────────────────────────────────

async def _render_pending(db: AsyncSession, master: Master) -> tuple[str, InlineKeyboardMarkup]:
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
        text = f"⏳ <b>Ожидают подтверждения ({len(bookings)}):</b>\n\n" + "\n".join(lines)

    buttons = []
    for b in bookings[:10]:
        buttons.append([
            InlineKeyboardButton(text=f"✅ {b.client_pseudo[:20]}", callback_data=f"bk_confirm:{b.id}"),
            InlineKeyboardButton(text="❌", callback_data=f"bk_reject:{b.id}"),
            InlineKeyboardButton(text="💬", callback_data=f"bk_msg:{b.id}"),
        ])

    tabs = booking_tabs_kb().inline_keyboard
    kb = InlineKeyboardMarkup(inline_keyboard=buttons + tabs)
    return text, kb


@router.message(Command("bookings"))
@router.message(F.text == "📖 Записи")
async def cmd_bookings(message: Message, db: AsyncSession, master: Master):
    text, kb = await _render_pending(db, master)
    await message.answer(text, reply_markup=kb)


@router.callback_query(F.data == "tab:pending")
async def tab_pending(callback: CallbackQuery, db: AsyncSession, master: Master):
    text, kb = await _render_pending(db, master)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


# ── Вкладка: Сегодня ──────────────────────────────────────────

@router.callback_query(F.data == "tab:today")
async def tab_today(callback: CallbackQuery, db: AsyncSession, master: Master):
    today = date.today()
    result = await db.execute(
        select(Booking)
        .options(selectinload(Booking.service))
        .where(
            Booking.master_id == master.id,
            Booking.booking_date == today,
            Booking.status.in_(["confirmed", "pending"]),
        )
        .order_by(Booking.start_time)
    )
    bookings = list(result.scalars().all())
    if not bookings:
        text = "📅 Сегодня записей нет."
    else:
        lines = [format_booking(b) for b in bookings]
        text = f"📅 <b>Сегодня ({len(bookings)}):</b>\n\n" + "\n".join(lines)

    buttons = []
    for b in bookings:
        if b.status == "confirmed":
            buttons.append([
                InlineKeyboardButton(
                    text=f"❌ Отменить: {b.client_pseudo[:20]}",
                    callback_data=f"bk_cancel:{b.id}",
                )
            ])

    tabs = booking_tabs_kb().inline_keyboard
    kb = InlineKeyboardMarkup(inline_keyboard=buttons + tabs)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


# ── Вкладка: Предстоящие ──────────────────────────────────────

@router.callback_query(F.data == "tab:upcoming")
async def tab_upcoming(callback: CallbackQuery, db: AsyncSession, master: Master):
    tomorrow = date.today() + timedelta(days=1)
    result = await db.execute(
        select(Booking)
        .options(selectinload(Booking.service))
        .where(
            Booking.master_id == master.id,
            Booking.status.in_(["confirmed", "pending"]),
            Booking.booking_date >= tomorrow,
        )
        .order_by(Booking.booking_date, Booking.start_time)
        .limit(20)
    )
    bookings = list(result.scalars().all())
    if not bookings:
        text = "📆 Нет предстоящих записей."
    else:
        lines = [format_booking(b) for b in bookings]
        text = f"📆 <b>Предстоящие ({len(bookings)}):</b>\n\n" + "\n".join(lines)
    await callback.message.edit_text(text, reply_markup=booking_tabs_kb())
    await callback.answer()


# ── Вкладка: История ──────────────────────────────────────────

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


# ── Подтверждение записи мастером ──────────────────────────────

@router.callback_query(F.data.startswith("bk_confirm:"))
async def bk_confirm(callback: CallbackQuery, db: AsyncSession, master: Master):
    booking_id = int(callback.data.split(":")[1])
    booking = await db.get(Booking, booking_id)
    if not booking or booking.master_id != master.id:
        await callback.answer("Запись не найдена", show_alert=True)
        return
    if booking.status != "pending":
        await callback.answer("Запись уже обработана", show_alert=True)
        return

    service = await db.get(Service, booking.service_id)

    booking.status = "confirmed"
    db.add(Event(master_id=master.id, event_type="booking_confirmed", payload={"booking_id": booking.id}))
    await db.commit()
    await callback.answer("✅ Запись подтверждена!")

    lang = getattr(master, "language", "ru") or "ru"
    min_unit = t(lang, "min_unit")
    price_str = fmt_price(service.price) if service else ""
    service_line = (
        t(lang, "service_line",
          service=service.name,
          duration=f"{service.duration_min} {min_unit}",
          price=price_str)
        if service else ""
    )
    await _notify_client(
        callback.bot, booking, db,
        t(lang, "booking_confirmed_client",
          master=master.display_name or "Мастер",
          service_line=service_line,
          date=booking.booking_date.strftime("%d.%m.%Y"),
          time=booking.start_time.strftime("%H:%M")),
    )

    await callback.message.edit_text(
        f"✅ Запись <b>{booking.client_pseudo}</b> подтверждена!",
        reply_markup=booking_tabs_kb(),
    )


# ── Отклонение записи мастером (с причиной) ───────────────────

@router.callback_query(F.data.startswith("bk_reject:"))
async def bk_reject(callback: CallbackQuery, db: AsyncSession, master: Master, state: FSMContext):
    booking_id = int(callback.data.split(":")[1])
    booking = await db.get(Booking, booking_id)
    if not booking or booking.master_id != master.id:
        await callback.answer("Запись не найдена", show_alert=True)
        return
    if booking.status != "pending":
        await callback.answer("Запись уже обработана", show_alert=True)
        return

    await state.update_data(reject_booking_id=booking_id)
    await state.set_state(MasterRejectReasonStates.TYPING)
    await callback.message.edit_text(
        f"Укажите причину отклонения записи <b>{booking.client_pseudo}</b> "
        f"(или /skip чтобы пропустить):"
    )
    await callback.answer()


@router.message(MasterRejectReasonStates.TYPING)
async def process_reject_reason(message: Message, db: AsyncSession, master: Master, state: FSMContext):
    data = await state.get_data()
    booking_id = data["reject_booking_id"]
    booking = await db.get(Booking, booking_id)
    if not booking:
        await state.clear()
        await message.answer("Запись не найдена.")
        return

    reason = None
    if message.text and message.text.strip() != "/skip":
        reason = message.text.strip()

    booking.status = "cancelled"
    booking.cancel_reason = reason
    db.add(Event(master_id=master.id, event_type="booking_cancelled", payload={"booking_id": booking.id}))
    await db.commit()

    reason_text = f"\nПричина: {reason}" if reason else ""
    await _notify_client(
        message.bot, booking, db,
        f"😔 К сожалению, мастер не смог принять вашу запись "
        f"на {booking.booking_date.strftime('%d.%m.%Y')} в {booking.start_time.strftime('%H:%M')}.{reason_text}",
    )

    await state.clear()
    await message.answer(
        f"❌ Запись <b>{booking.client_pseudo}</b> отклонена.",
        reply_markup=booking_tabs_kb(),
    )


# ── Отмена подтверждённой записи мастером ──────────────────────

@router.callback_query(F.data.startswith("bk_cancel:"))
async def bk_cancel(callback: CallbackQuery, db: AsyncSession, master: Master, state: FSMContext):
    booking_id = int(callback.data.split(":")[1])
    booking = await db.get(Booking, booking_id)
    if not booking or booking.master_id != master.id:
        await callback.answer("Запись не найдена", show_alert=True)
        return
    if booking.status not in ("pending", "confirmed"):
        await callback.answer("Эту запись нельзя отменить", show_alert=True)
        return

    await state.update_data(cancel_booking_id=booking_id)
    await state.set_state(MasterCancelReasonStates.TYPING)

    svc = await db.get(Service, booking.service_id)
    svc_name = svc.name if svc else "—"
    await callback.message.edit_text(
        f"Отмена записи:\n"
        f"👤 {booking.client_pseudo}\n"
        f"💅 {svc_name} · {booking.booking_date.strftime('%d.%m')} в {booking.start_time.strftime('%H:%M')}\n\n"
        f"Укажите причину отмены (или /skip чтобы пропустить):"
    )
    await callback.answer()


@router.message(MasterCancelReasonStates.TYPING)
async def process_cancel_reason(message: Message, db: AsyncSession, master: Master, state: FSMContext):
    data = await state.get_data()
    booking_id = data["cancel_booking_id"]
    booking = await db.get(Booking, booking_id)
    if not booking:
        await state.clear()
        await message.answer("Запись не найдена.")
        return

    reason = None
    if message.text and message.text.strip() != "/skip":
        reason = message.text.strip()

    booking.status = "cancelled"
    booking.cancel_reason = reason
    db.add(Event(master_id=master.id, event_type="booking_cancelled", payload={"booking_id": booking.id}))
    await db.commit()

    svc = await db.get(Service, booking.service_id)
    svc_name = svc.name if svc else "—"
    reason_text = f"\nПричина: {reason}" if reason else ""

    await _notify_client(
        message.bot, booking, db,
        f"❌ Мастер отменил вашу запись\n\n"
        f"💅 {svc_name} · {booking.booking_date.strftime('%d.%m.%Y')} · {booking.start_time.strftime('%H:%M')}"
        f"{reason_text}",
    )

    await state.clear()
    await message.answer(
        f"❌ Запись <b>{booking.client_pseudo}</b> отменена.",
        reply_markup=booking_tabs_kb(),
    )


# ── Анонимная переписка: мастер → клиент ──────────────────────

@router.callback_query(F.data.startswith("bk_msg:"))
async def bk_msg_start(callback: CallbackQuery, db: AsyncSession, master: Master, state: FSMContext):
    booking_id = int(callback.data.split(":")[1])
    booking = await db.get(Booking, booking_id)
    if not booking or booking.master_id != master.id:
        await callback.answer("Запись не найдена", show_alert=True)
        return

    await state.update_data(msg_booking_id=booking_id)
    await state.set_state(MasterMessageStates.TYPING)
    await callback.message.answer(
        f"Напишите сообщение для клиента <b>{booking.client_pseudo}</b>:"
    )
    await callback.answer()


@router.message(MasterMessageStates.TYPING)
async def process_master_message(message: Message, db: AsyncSession, master: Master, state: FSMContext):
    data = await state.get_data()
    booking_id = data["msg_booking_id"]
    booking = await db.get(Booking, booking_id)
    if not booking:
        await state.clear()
        await message.answer("Запись не найдена.")
        return

    text = message.text or ""
    if not text.strip():
        await message.answer("Сообщение не может быть пустым. Попробуйте ещё раз:")
        return

    # Save message
    db.add(BotMessage(booking_id=booking_id, from_role="master", text=text.strip()))
    await db.commit()

    # Relay to client
    await _notify_client(
        message.bot, booking, db,
        f"Мастер написал вам по записи на "
        f"{booking.booking_date.strftime('%d.%m')} в {booking.start_time.strftime('%H:%M')}:\n\n"
        f"«{text.strip()}»",
        reply_kb_booking_id=booking_id,
    )

    await state.clear()
    await message.answer(f"✅ Сообщение отправлено клиенту <b>{booking.client_pseudo}</b>.")


# ── Анонимная переписка: клиент → мастер ──────────────────────

@router.callback_query(F.data.startswith("cl_reply:"))
async def cl_reply_start(callback: CallbackQuery, state: FSMContext):
    booking_id = int(callback.data.split(":")[1])
    await state.update_data(reply_booking_id=booking_id)
    await state.set_state(ClientReplyStates.TYPING)
    await callback.message.answer("Напишите ваш ответ мастеру:")
    await callback.answer()


@router.message(ClientReplyStates.TYPING)
async def process_client_reply(message: Message, db: AsyncSession, state: FSMContext):
    data = await state.get_data()
    booking_id = data.get("reply_booking_id")
    if not booking_id:
        await state.clear()
        return

    booking = await db.get(Booking, booking_id)
    if not booking:
        await state.clear()
        await message.answer("Запись не найдена.")
        return

    text = (message.text or "").strip()
    if not text:
        await message.answer("Сообщение не может быть пустым:")
        return

    # Save message
    db.add(BotMessage(booking_id=booking_id, from_role="client", text=text))
    await db.commit()

    # Relay to master
    master = await db.get(Master, booking.master_id)
    if master:
        try:
            await message.bot.send_message(
                master.telegram_id,
                f"💬 <b>{booking.client_pseudo}</b> ответил по записи "
                f"на {booking.booking_date.strftime('%d.%m')} в {booking.start_time.strftime('%H:%M')}:\n\n"
                f"«{text}»",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="💬 Ответить", callback_data=f"bk_msg:{booking_id}")],
                ]),
            )
        except Exception:
            pass

    await state.clear()
    await message.answer("✅ Ваш ответ отправлен мастеру.")


# ── Отмена записи клиентом ─────────────────────────────────────

@router.callback_query(F.data.startswith("cl_cancel:"))
async def cl_cancel(callback: CallbackQuery, db: AsyncSession):
    booking_id = int(callback.data.split(":")[1])
    booking = await db.get(Booking, booking_id)
    if not booking:
        await callback.answer("Запись не найдена", show_alert=True)
        return
    if booking.status not in ("pending", "confirmed"):
        await callback.answer("Эту запись уже нельзя отменить", show_alert=True)
        return

    svc = await db.get(Service, booking.service_id)
    svc_name = svc.name if svc else "—"
    await callback.message.edit_text(
        f"Вы уверены?\n"
        f"💅 {svc_name} · {booking.booking_date.strftime('%d.%m.%Y')} · {booking.start_time.strftime('%H:%M')}",
        reply_markup=client_cancel_confirm_kb(booking_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cl_cancel_yes:"))
async def cl_cancel_yes(callback: CallbackQuery, db: AsyncSession):
    booking_id = int(callback.data.split(":")[1])
    booking = await db.get(Booking, booking_id)
    if not booking:
        await callback.answer("Запись не найдена", show_alert=True)
        return
    if booking.status not in ("pending", "confirmed"):
        await callback.answer("Эту запись уже нельзя отменить", show_alert=True)
        return

    booking.status = "cancelled"
    booking.cancel_reason = "Отменено клиентом"
    db.add(Event(master_id=booking.master_id, event_type="booking_cancelled", payload={
        "booking_id": booking.id, "cancelled_by": "client",
    }))
    await db.commit()

    await callback.message.edit_text("✅ Запись отменена.")

    # Notify master
    master = await db.get(Master, booking.master_id)
    if master:
        try:
            await callback.bot.send_message(
                master.telegram_id,
                f"❌ Клиент <b>{booking.client_pseudo}</b> отменил запись "
                f"на {booking.booking_date.strftime('%d.%m.%Y')} в {booking.start_time.strftime('%H:%M')}.\n"
                f"Слот освобождён.",
            )
        except Exception:
            pass

    await callback.answer()


@router.callback_query(F.data.startswith("cl_cancel_no:"))
async def cl_cancel_no(callback: CallbackQuery):
    await callback.message.edit_text("👍 Запись сохранена.")
    await callback.answer()


# ── Helpers ────────────────────────────────────────────────────

async def _find_client_tg_id(booking: Booking) -> int | None:
    """Lookup client telegram_id from tg_hash via Redis cache."""
    if not booking.client_tg_hash:
        return None
    try:
        from redis.asyncio import from_url
        from shared.config import settings
        redis = from_url(settings.redis_url)
        tg_id_bytes = await redis.get(f"tghash:{booking.client_tg_hash}")
        await redis.aclose()
        if tg_id_bytes:
            return int(tg_id_bytes)
    except Exception as e:
        logger.warning(f"Failed to lookup client tg_id: {e}")
    return None


async def _notify_client(
    bot,
    booking: Booking,
    db: AsyncSession,
    text: str,
    reply_kb_booking_id: int | None = None,
):
    """Send a message to the client identified by tg_hash (via Redis reverse lookup)."""
    client_tg_id = await _find_client_tg_id(booking)
    if not client_tg_id:
        return

    kb = None
    if reply_kb_booking_id:
        kb = client_reply_kb(reply_kb_booking_id)

    try:
        await bot.send_message(client_tg_id, text, reply_markup=kb)
    except Exception as e:
        logger.warning(f"Failed to notify client: {e}")

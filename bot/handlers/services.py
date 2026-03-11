from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.states.onboarding import AddServiceStates, EditServiceStates
from db.models import Master, Service
from shared.config import settings

router = Router()


def fmt_price(price: int | None, currency: str = "RUB") -> str:
    from shared.i18n import fmt_price as _fmt
    return _fmt(price, currency, "ru")


def price_ask_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    from shared.i18n import t as _t
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=_t(lang, "skip_price_btn"), callback_data="skip_price"),
    ]])


def services_list_kb(services: list[Service], currency: str = "RUB") -> InlineKeyboardMarkup:
    buttons = []
    for s in services:
        status = "✅" if s.is_active else "🙈"
        buttons.append([
            InlineKeyboardButton(
                text=f"{status} {s.name} — {fmt_price(s.price, currency)} ({s.duration_min} мин)",
                callback_data=f"svc_view:{s.id}",
            )
        ])
    buttons.append([InlineKeyboardButton(text="➕ Добавить услугу", callback_data="svc_add")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def service_actions_kb(service_id: int, is_active: bool) -> InlineKeyboardMarkup:
    hide_text = "🙈 Скрыть" if is_active else "👁 Показать"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"svc_edit:{service_id}"),
                InlineKeyboardButton(text=hide_text, callback_data=f"svc_toggle:{service_id}"),
            ],
            [
                InlineKeyboardButton(text="🗑 Удалить", callback_data=f"svc_del:{service_id}"),
                InlineKeyboardButton(text="⬅️ Назад", callback_data="svc_back"),
            ],
        ]
    )


@router.message(Command("services"))
@router.message(F.text == "📋 Услуги")
async def cmd_services(message: Message, db: AsyncSession, master: Master):
    result = await db.execute(
        select(Service).where(Service.master_id == master.id).order_by(Service.sort_order)
    )
    services = list(result.scalars().all())

    if not services:
        await message.answer(
            "У вас пока нет услуг.\nДобавьте первую!",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="➕ Добавить услугу", callback_data="svc_add")]]
            ),
        )
        return

    await message.answer("📋 <b>Ваши услуги:</b>", reply_markup=services_list_kb(services, master.currency or "RUB"))


@router.callback_query(F.data == "svc_back")
async def svc_back(callback: CallbackQuery, db: AsyncSession, master: Master):
    result = await db.execute(
        select(Service).where(Service.master_id == master.id).order_by(Service.sort_order)
    )
    services = list(result.scalars().all())
    await callback.message.edit_text("📋 <b>Ваши услуги:</b>", reply_markup=services_list_kb(services, master.currency or "RUB"))
    await callback.answer()


@router.callback_query(F.data.startswith("svc_view:"))
async def svc_view(callback: CallbackQuery, db: AsyncSession, master: Master):
    service_id = int(callback.data.split(":")[1])
    service = await db.get(Service, service_id)
    if not service:
        await callback.answer("Услуга не найдена", show_alert=True)
        return
    currency = master.currency or "RUB"
    text = (
        f"📋 <b>{service.name}</b>\n\n"
        f"💰 Цена: {fmt_price(service.price, currency)}\n"
        f"⏱ Длительность: {service.duration_min} мин\n"
        f"📝 Описание: {service.description or '—'}\n"
        f"Статус: {'✅ Активна' if service.is_active else '🙈 Скрыта'}"
    )
    await callback.message.edit_text(text, reply_markup=service_actions_kb(service.id, service.is_active))
    await callback.answer()


@router.callback_query(F.data.startswith("svc_toggle:"))
async def svc_toggle(callback: CallbackQuery, db: AsyncSession, master: Master):
    service_id = int(callback.data.split(":")[1])
    service = await db.get(Service, service_id)
    if not service:
        await callback.answer("Услуга не найдена", show_alert=True)
        return
    service.is_active = not service.is_active
    await db.commit()
    status = "показана клиентам" if service.is_active else "скрыта от клиентов"
    await callback.answer(f"Услуга {status}")
    # Refresh view
    currency = master.currency or "RUB"
    text = (
        f"📋 <b>{service.name}</b>\n\n"
        f"💰 Цена: {fmt_price(service.price, currency)}\n"
        f"⏱ Длительность: {service.duration_min} мин\n"
        f"Статус: {'✅ Активна' if service.is_active else '🙈 Скрыта'}"
    )
    await callback.message.edit_text(text, reply_markup=service_actions_kb(service.id, service.is_active))


@router.callback_query(F.data.startswith("svc_edit:"))
async def svc_edit_start(callback: CallbackQuery, state: FSMContext, db: AsyncSession, master: Master):
    service_id = int(callback.data.split(":")[1])
    service = await db.get(Service, service_id)
    if not service:
        await callback.answer("Услуга не найдена", show_alert=True)
        return
    currency = master.currency or "RUB"
    await state.update_data(service_id=service_id, currency=currency)
    await callback.message.answer(
        f"✏️ Редактирование: <b>{service.name}</b>\n\n"
        f"Что изменить?\n"
        f"• /svc_name — название (сейчас: {service.name})\n"
        f"• /svc_price — цена (сейчас: {fmt_price(service.price, currency)})\n"
        f"• /svc_duration — длительность (сейчас: {service.duration_min} мин)\n\n"
        "Отправьте одну из команд выше или /cancel для отмены."
    )
    await state.set_state(EditServiceStates.FIELD)
    await callback.answer()


@router.message(EditServiceStates.FIELD, F.text.in_({"/svc_name", "/svc_price", "/svc_duration"}))
async def svc_edit_field(message: Message, state: FSMContext):
    field_map = {"/svc_name": "name", "/svc_price": "price", "/svc_duration": "duration"}
    field = field_map[message.text]
    prompts = {
        "name": "Введите новое <b>название</b> услуги (1–128 символов):",
        "price": "Введите новую <b>цену</b> (число от 0 до 1 000 000) или /skip для «по договорённости»:",
        "duration": "Введите новую <b>длительность</b> в минутах (5–480):",
    }
    await state.update_data(edit_field=field)
    await message.answer(prompts[field])
    await state.set_state(EditServiceStates.VALUE)


@router.message(EditServiceStates.FIELD, F.text == "/cancel")
async def svc_edit_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено.")


@router.message(EditServiceStates.VALUE)
async def svc_edit_value(message: Message, state: FSMContext, db: AsyncSession):
    data = await state.get_data()
    service_id = data["service_id"]
    field = data["edit_field"]
    currency = data.get("currency", "RUB")
    text = (message.text or "").strip()

    service = await db.get(Service, service_id)
    if not service:
        await state.clear()
        await message.answer("Услуга не найдена.")
        return

    if field == "name":
        if len(text) < 1 or len(text) > 128:
            await message.answer("Название — от 1 до 128 символов. Попробуйте ещё раз:")
            return
        service.name = text
        await db.commit()
        await state.clear()
        await message.answer(f"✅ Название обновлено: <b>{text}</b>")

    elif field == "price":
        if text == "/skip":
            service.price = None
            await db.commit()
            await state.clear()
            await message.answer("✅ Цена обновлена: <b>по договорённости</b>")
            return
        try:
            price = int(text)
            if price < 0 or price > 1_000_000:
                raise ValueError
        except ValueError:
            await message.answer("Введите цену числом от 0 до 1 000 000 или /skip:")
            return
        service.price = price
        await db.commit()
        await state.clear()
        await message.answer(f"✅ Цена обновлена: <b>{fmt_price(price, currency)}</b>")

    elif field == "duration":
        try:
            duration = int(text)
            if duration < 5 or duration > 480:
                raise ValueError
        except ValueError:
            await message.answer("Длительность — от 5 до 480 минут. Попробуйте ещё раз:")
            return
        service.duration_min = duration
        await db.commit()
        await state.clear()
        await message.answer(f"✅ Длительность обновлена: <b>{duration} мин</b>")


@router.callback_query(F.data.startswith("svc_del:"))
async def svc_delete(callback: CallbackQuery, db: AsyncSession, master: Master):
    service_id = int(callback.data.split(":")[1])
    service = await db.get(Service, service_id)
    if service:
        await db.delete(service)
        await db.commit()
    await callback.answer("Услуга удалена")
    # Go back to list
    await svc_back(callback, db, master)


# ── Add service FSM ──────────────────────────────────────────

@router.callback_query(F.data == "svc_add")
async def svc_add_start(callback: CallbackQuery, state: FSMContext, db: AsyncSession, master: Master):
    # Check free tier limit
    if master.subscription_status != "active":
        result = await db.execute(
            select(Service).where(Service.master_id == master.id)
        )
        count = len(list(result.scalars().all()))
        if count >= settings.free_tier_max_services:
            await callback.answer(
                f"На бесплатном тарифе максимум {settings.free_tier_max_services} услуги. "
                "Оформите подписку для безлимита.",
                show_alert=True,
            )
            return

    await state.update_data(currency=master.currency or "RUB")
    await callback.message.edit_text("Введите <b>название</b> новой услуги:")
    await state.set_state(AddServiceStates.NAME)
    await callback.answer()


@router.message(AddServiceStates.NAME)
async def add_svc_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 1 or len(name) > 128:
        await message.answer("Название — от 1 до 128 символов:")
        return
    await state.update_data(name=name)
    await message.answer(
        f"Услуга: <b>{name}</b>\n\nУкажите <b>цену</b> или пропустите, если цена индивидуальная:",
        reply_markup=price_ask_kb(),
    )
    await state.set_state(AddServiceStates.PRICE)


@router.message(AddServiceStates.PRICE)
async def add_svc_price(message: Message, state: FSMContext):
    try:
        price = int(message.text.strip())
        if price < 0 or price > 1_000_000:
            raise ValueError
    except ValueError:
        await message.answer("Введите цену числом от 0 до 1 000 000:", reply_markup=price_ask_kb())
        return
    data = await state.get_data()
    currency = data.get("currency", "RUB")
    await state.update_data(price=price)
    await message.answer(f"Цена: <b>{fmt_price(price, currency)}</b>\n\nУкажите <b>длительность в минутах</b>:")
    await state.set_state(AddServiceStates.DURATION)


@router.callback_query(AddServiceStates.PRICE, F.data == "skip_price")
async def add_svc_skip_price(callback: CallbackQuery, state: FSMContext):
    await state.update_data(price=None)
    await callback.message.edit_text("Цена: <b>по договорённости</b>\n\nУкажите <b>длительность в минутах</b>:")
    await state.set_state(AddServiceStates.DURATION)
    await callback.answer()


@router.message(AddServiceStates.DURATION)
async def add_svc_duration(message: Message, state: FSMContext, db: AsyncSession, master: Master):
    try:
        duration = int(message.text.strip())
        if duration < 5 or duration > 480:
            raise ValueError
    except ValueError:
        await message.answer("Длительность — от 5 до 480 минут:")
        return

    data = await state.get_data()
    service = Service(
        master_id=master.id,
        name=data["name"],
        price=data["price"],
        duration_min=duration,
    )
    db.add(service)
    await db.commit()
    await state.clear()
    currency = data.get("currency", "RUB")
    await message.answer(
        f"✅ Услуга <b>{data['name']}</b> добавлена!\n"
        f"💰 {fmt_price(data.get('price'), currency)} · ⏱ {duration} мин\n\n"
        "Используйте /services для управления услугами."
    )

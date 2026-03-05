from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.states.onboarding import AddServiceStates
from db.models import Master, Service
from shared.config import settings

router = Router()


def services_list_kb(services: list[Service]) -> InlineKeyboardMarkup:
    buttons = []
    for s in services:
        status = "✅" if s.is_active else "🙈"
        buttons.append([
            InlineKeyboardButton(
                text=f"{status} {s.name} — {s.price} ₽ ({s.duration_min} мин)",
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

    await message.answer("📋 <b>Ваши услуги:</b>", reply_markup=services_list_kb(services))


@router.callback_query(F.data == "svc_back")
async def svc_back(callback: CallbackQuery, db: AsyncSession, master: Master):
    result = await db.execute(
        select(Service).where(Service.master_id == master.id).order_by(Service.sort_order)
    )
    services = list(result.scalars().all())
    await callback.message.edit_text("📋 <b>Ваши услуги:</b>", reply_markup=services_list_kb(services))
    await callback.answer()


@router.callback_query(F.data.startswith("svc_view:"))
async def svc_view(callback: CallbackQuery, db: AsyncSession):
    service_id = int(callback.data.split(":")[1])
    service = await db.get(Service, service_id)
    if not service:
        await callback.answer("Услуга не найдена", show_alert=True)
        return
    text = (
        f"📋 <b>{service.name}</b>\n\n"
        f"💰 Цена: {service.price} ₽\n"
        f"⏱ Длительность: {service.duration_min} мин\n"
        f"📝 Описание: {service.description or '—'}\n"
        f"Статус: {'✅ Активна' if service.is_active else '🙈 Скрыта'}"
    )
    await callback.message.edit_text(text, reply_markup=service_actions_kb(service.id, service.is_active))
    await callback.answer()


@router.callback_query(F.data.startswith("svc_toggle:"))
async def svc_toggle(callback: CallbackQuery, db: AsyncSession):
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
    text = (
        f"📋 <b>{service.name}</b>\n\n"
        f"💰 Цена: {service.price} ₽\n"
        f"⏱ Длительность: {service.duration_min} мин\n"
        f"Статус: {'✅ Активна' if service.is_active else '🙈 Скрыта'}"
    )
    await callback.message.edit_text(text, reply_markup=service_actions_kb(service.id, service.is_active))


@router.callback_query(F.data.startswith("svc_del:"))
async def svc_delete(callback: CallbackQuery, db: AsyncSession):
    service_id = int(callback.data.split(":")[1])
    service = await db.get(Service, service_id)
    if service:
        await db.delete(service)
        await db.commit()
    await callback.answer("Услуга удалена")
    # Go back to list
    await svc_back(callback, db, None)


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
    await message.answer(f"Услуга: <b>{name}</b>\n\nУкажите <b>цену в рублях</b>:")
    await state.set_state(AddServiceStates.PRICE)


@router.message(AddServiceStates.PRICE)
async def add_svc_price(message: Message, state: FSMContext):
    try:
        price = int(message.text.strip())
        if price < 0 or price > 1_000_000:
            raise ValueError
    except ValueError:
        await message.answer("Введите цену числом от 0 до 1 000 000:")
        return
    await state.update_data(price=price)
    await message.answer(f"Цена: <b>{price} ₽</b>\n\nУкажите <b>длительность в минутах</b>:")
    await state.set_state(AddServiceStates.DURATION)


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
    await message.answer(
        f"✅ Услуга <b>{data['name']}</b> добавлена!\n"
        f"💰 {data['price']} ₽ · ⏱ {duration} мин\n\n"
        "Используйте /services для управления услугами."
    )

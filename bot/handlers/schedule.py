from datetime import time as dt_time

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.common import WEEKDAYS
from bot.states.onboarding import EditScheduleStates
from db.models import Master, ScheduleTemplate

router = Router()


def schedule_overview_kb(templates: dict[int, ScheduleTemplate]) -> InlineKeyboardMarkup:
    buttons = []
    for i, day_name in enumerate(WEEKDAYS):
        t = templates.get(i)
        if t and t.is_working:
            text = f"✅ {day_name} {t.start_time.strftime('%H:%M')}–{t.end_time.strftime('%H:%M')}"
        else:
            text = f"❌ {day_name} — выходной"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"sched_day:{i}")])
    buttons.append([
        InlineKeyboardButton(text="🚫 Заблокировать дату", callback_data="sched_block"),
        InlineKeyboardButton(text="➕ Рабочий день", callback_data="sched_add_day"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("schedule"))
@router.message(F.text == "📅 Расписание")
async def cmd_schedule(message: Message, db: AsyncSession, master: Master):
    result = await db.execute(
        select(ScheduleTemplate).where(ScheduleTemplate.master_id == master.id)
    )
    templates = {t.day_of_week: t for t in result.scalars().all()}
    await message.answer(
        "📅 <b>Ваше расписание:</b>\n\nНажмите на день чтобы изменить:",
        reply_markup=schedule_overview_kb(templates),
    )


@router.callback_query(F.data.startswith("sched_day:"))
async def sched_edit_day(callback: CallbackQuery, state: FSMContext, db: AsyncSession, master: Master):
    day = int(callback.data.split(":")[1])
    result = await db.execute(
        select(ScheduleTemplate).where(
            ScheduleTemplate.master_id == master.id,
            ScheduleTemplate.day_of_week == day,
        )
    )
    template = result.scalar_one_or_none()

    if template and template.is_working:
        # Toggle to day off
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="⏰ Изменить время", callback_data=f"sched_time:{day}"),
                    InlineKeyboardButton(text="❌ Сделать выходным", callback_data=f"sched_off:{day}"),
                ],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="sched_back")],
            ]
        )
        await callback.message.edit_text(
            f"<b>{WEEKDAYS[day]}</b>: {template.start_time.strftime('%H:%M')}–{template.end_time.strftime('%H:%M')}, "
            f"шаг {template.slot_step_min} мин",
            reply_markup=kb,
        )
    else:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✅ Сделать рабочим", callback_data=f"sched_time:{day}")],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="sched_back")],
            ]
        )
        await callback.message.edit_text(f"<b>{WEEKDAYS[day]}</b> — выходной", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("sched_off:"))
async def sched_off(callback: CallbackQuery, db: AsyncSession, master: Master):
    day = int(callback.data.split(":")[1])
    result = await db.execute(
        select(ScheduleTemplate).where(
            ScheduleTemplate.master_id == master.id,
            ScheduleTemplate.day_of_week == day,
        )
    )
    template = result.scalar_one_or_none()
    if template:
        template.is_working = False
        await db.commit()
    await callback.answer(f"{WEEKDAYS[day]} — теперь выходной")
    # Refresh
    result = await db.execute(
        select(ScheduleTemplate).where(ScheduleTemplate.master_id == master.id)
    )
    templates = {t.day_of_week: t for t in result.scalars().all()}
    await callback.message.edit_text(
        "📅 <b>Ваше расписание:</b>\n\nНажмите на день чтобы изменить:",
        reply_markup=schedule_overview_kb(templates),
    )


@router.callback_query(F.data == "sched_back")
async def sched_back(callback: CallbackQuery, db: AsyncSession, master: Master):
    result = await db.execute(
        select(ScheduleTemplate).where(ScheduleTemplate.master_id == master.id)
    )
    templates = {t.day_of_week: t for t in result.scalars().all()}
    await callback.message.edit_text(
        "📅 <b>Ваше расписание:</b>\n\nНажмите на день чтобы изменить:",
        reply_markup=schedule_overview_kb(templates),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("sched_time:"))
async def sched_time_start(callback: CallbackQuery, state: FSMContext):
    day = int(callback.data.split(":")[1])
    await state.update_data(edit_day=day)
    await callback.message.edit_text(
        f"Введите <b>время начала</b> для {WEEKDAYS[day]} (например: 9:00):"
    )
    await state.set_state(EditScheduleStates.START_TIME)
    await callback.answer()


@router.message(EditScheduleStates.START_TIME)
async def edit_start_time(message: Message, state: FSMContext):
    try:
        parts = message.text.strip().replace(".", ":").split(":")
        hour, minute = int(parts[0]), int(parts[1]) if len(parts) > 1 else 0
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
    except (ValueError, IndexError):
        await message.answer("Формат ЧЧ:ММ (например: 9:00):")
        return
    await state.update_data(start_h=hour, start_m=minute)
    await message.answer(f"Начало: {hour:02d}:{minute:02d}\n\nВведите <b>время конца</b>:")
    await state.set_state(EditScheduleStates.END_TIME)


@router.message(EditScheduleStates.END_TIME)
async def edit_end_time(message: Message, state: FSMContext, db: AsyncSession, master: Master):
    try:
        parts = message.text.strip().replace(".", ":").split(":")
        hour, minute = int(parts[0]), int(parts[1]) if len(parts) > 1 else 0
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
    except (ValueError, IndexError):
        await message.answer("Формат ЧЧ:ММ:")
        return

    data = await state.get_data()
    start_total = data["start_h"] * 60 + data["start_m"]
    end_total = hour * 60 + minute
    if end_total <= start_total:
        await message.answer("Конец дня должен быть позже начала:")
        return

    day = data["edit_day"]
    start_time = dt_time(data["start_h"], data["start_m"])
    end_time = dt_time(hour, minute)

    result = await db.execute(
        select(ScheduleTemplate).where(
            ScheduleTemplate.master_id == master.id,
            ScheduleTemplate.day_of_week == day,
        )
    )
    template = result.scalar_one_or_none()
    if template:
        template.start_time = start_time
        template.end_time = end_time
        template.is_working = True
    else:
        template = ScheduleTemplate(
            master_id=master.id,
            day_of_week=day,
            start_time=start_time,
            end_time=end_time,
            is_working=True,
        )
        db.add(template)
    await db.commit()
    await state.clear()
    await message.answer(
        f"✅ {WEEKDAYS[day]}: {start_time.strftime('%H:%M')}–{end_time.strftime('%H:%M')}\n\n"
        "Используйте /schedule для просмотра."
    )

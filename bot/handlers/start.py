import logging
from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.filters import Command, CommandStart, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, MenuButtonWebApp, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.services import fmt_price, price_ask_kb
from bot.keyboards.common import niche_kb, schedule_days_kb, slot_step_kb, main_menu_kb
from bot.states.onboarding import OnboardingStates
from db.models import Master, Service, ScheduleTemplate, ScheduleOverride, Event, Referral
from shared.config import settings
from shared.utils import generate_referral_code

router = Router()
logger = logging.getLogger(__name__)

WELCOME_TEXT = (
    "👋 <b>Добро пожаловать в Plotina bot!</b>\n\n"
    "Я помогаю мастерам и специалистам принимать онлайн-запись от клиентов — "
    "без мессенджеров, таблиц и путаницы.\n\n"
    "❌ <b>Знакомо?</b>\n"
    "• Клиенты пишут в личку — записи теряются\n"
    "• Сложно отслеживать, кто на когда записан\n"
    "• Нет удобного способа поделиться расписанием\n\n"
    "✅ <b>Что умеет бот:</b>\n"
    "📅 Принимать запись 24/7 без вашего участия\n"
    "👥 Вести список клиентов с историей визитов\n"
    "🔔 Напоминать клиентам о записи за 24 ч и 2 ч\n"
    "📨 Отправлять рассылки своей базе клиентов\n\n"
    "🚀 <b>Как это работает:</b>\n"
    "1. Настройте профиль (~2 минуты)\n"
    "2. Поделитесь ссылкой с клиентами\n"
    "3. Клиенты записываются сами — всё видно здесь\n\n"
    "─────────────────────────\n"
    "📜 <b>Согласие на обработку персональных данных</b>\n\n"
    "Нажимая «Принять и начать», вы даёте согласие на обработку ваших "
    "персональных данных (имя, юзернейм Telegram, Telegram ID) командой бота "
    "<b>Plotina bot</b> в целях предоставления сервиса онлайн-записи.\n\n"
    "Данные не передаются третьим лицам."
)

RESET_CONSENT_TEXT = (
    "🔄 <b>Начнём настройку заново!</b>\n\n"
    "📜 <b>Согласие на обработку персональных данных</b>\n\n"
    "Нажимая «Принять и продолжить», вы подтверждаете согласие на обработку "
    "ваших персональных данных (имя, юзернейм Telegram, Telegram ID) командой "
    "бота <b>Plotina bot</b> в целях предоставления сервиса онлайн-записи.\n\n"
    "Данные не передаются третьим лицам."
)


def consent_kb(action: str = "new") -> InlineKeyboardMarkup:
    label = "✅ Принять и начать" if action == "new" else "✅ Принять и продолжить"
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=label, callback_data=f"consent:{action}")
    ]])


async def log_event(db: AsyncSession, master_id: int | None, event_type: str, payload: dict | None = None):
    event = Event(master_id=master_id, event_type=event_type, payload=payload or {})
    db.add(event)
    await db.commit()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, db: AsyncSession, command: CommandObject):
    telegram_id = message.from_user.id

    # Always clear FSM state to avoid being stuck
    await state.clear()

    # If the user came via a client booking link (?start=book_username),
    # redirect them to the Mini App — do NOT start master onboarding.
    if command.args and command.args.startswith("book_"):
        master_username = command.args[5:]
        await message.answer(
            "Нажмите кнопку ниже, чтобы записаться к мастеру:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text="📅 Записаться",
                    web_app=WebAppInfo(url=f"{settings.miniapp_url}?master={master_username}"),
                )
            ]]),
        )
        return

    # Check if master already exists
    result = await db.execute(select(Master).where(Master.telegram_id == telegram_id))
    master = result.scalar_one_or_none()

    if master:
        # Reset existing master and restart onboarding from scratch
        await db.execute(
            ScheduleTemplate.__table__.delete().where(ScheduleTemplate.master_id == master.id)
        )
        await db.execute(
            ScheduleOverride.__table__.delete().where(ScheduleOverride.master_id == master.id)
        )
        await db.execute(
            Service.__table__.delete().where(Service.master_id == master.id)
        )
        master.is_onboarded = False
        master.display_name = None
        master.niche = None
        master.bio = None
        await db.commit()
        # Store existing master ID so process_step can update instead of insert
        await state.update_data(existing_master_id=master.id)
        await message.answer(RESET_CONSENT_TEXT, reply_markup=consent_kb("reset"))
        await state.set_state(OnboardingStates.CONSENT)
        return

    # [DISABLED - referral] Parse referral code from deep link: /start ref_XXXX
    # referrer_id = None
    # if command.args and command.args.startswith("ref_"):
    #     ref_code = command.args[4:]
    #     result = await db.execute(select(Master).where(Master.referral_code == ref_code))
    #     referrer = result.scalar_one_or_none()
    #     if referrer and referrer.telegram_id != telegram_id:
    #         referrer_id = referrer.id

    # New master — show welcome + consent
    await state.update_data(referrer_id=None)
    await message.answer(WELCOME_TEXT, reply_markup=consent_kb("new"))
    await state.set_state(OnboardingStates.CONSENT)


# ── Шаг 0: Согласие ──────────────────────────────────────────────

@router.callback_query(OnboardingStates.CONSENT, F.data.startswith("consent:"))
async def process_consent(callback: CallbackQuery, state: FSMContext):
    await state.update_data(
        consent_given=True,
        consent_at=datetime.utcnow().isoformat(),
    )
    await callback.message.edit_text(
        "Отлично! Давайте настроим ваш профиль.\n\n"
        "Как вас называть клиентам?\n"
        "(Можно имя, название студии или любой псевдоним)"
    )
    await state.set_state(OnboardingStates.NAME)
    await callback.answer()


# ── Шаг 1: Имя ──────────────────────────────────────────────────

@router.message(OnboardingStates.NAME)
async def process_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2 or len(name) > 64:
        await message.answer("Имя должно быть от 2 до 64 символов. Попробуйте ещё раз:")
        return
    await state.update_data(display_name=name)
    await message.answer(
        f"Отлично, {name}! 👋\n\nВыберите вашу сферу деятельности:",
        reply_markup=niche_kb(),
    )
    await state.set_state(OnboardingStates.NICHE)


# ── Шаг 2: Ниша ─────────────────────────────────────────────────

@router.callback_query(OnboardingStates.NICHE, F.data.startswith("niche:"))
async def process_niche(callback: CallbackQuery, state: FSMContext):
    niche = callback.data.split(":")[1]
    await state.update_data(niche=niche)
    await callback.message.edit_text(
        "Теперь добавим вашу первую услугу.\n\n"
        "Введите <b>название услуги</b>:\n"
        "(например: Стрижка, Маникюр, Урок английского)"
    )
    await state.set_state(OnboardingStates.SERVICE_NAME)
    await callback.answer()


# ── Шаг 3: Услуга ───────────────────────────────────────────────

@router.message(OnboardingStates.SERVICE_NAME)
async def process_service_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 1 or len(name) > 128:
        await message.answer("Название услуги — от 1 до 128 символов. Попробуйте ещё раз:")
        return
    await state.update_data(service_name=name)
    await message.answer(
        f"Услуга: <b>{name}</b>\n\n"
        "Укажите <b>цену в рублях</b> или пропустите, если цена индивидуальная:",
        reply_markup=price_ask_kb(),
    )
    await state.set_state(OnboardingStates.SERVICE_PRICE)


@router.message(OnboardingStates.SERVICE_PRICE)
async def process_service_price(message: Message, state: FSMContext):
    try:
        price = int(message.text.strip())
        if price < 0 or price > 1_000_000:
            raise ValueError
    except ValueError:
        await message.answer("Введите цену числом от 0 до 1 000 000:", reply_markup=price_ask_kb())
        return
    await state.update_data(service_price=price)
    await message.answer(
        f"Цена: <b>{price} ₽</b>\n\n"
        "Укажите <b>длительность в минутах</b> (только число):\n"
        "(например: 30, 60, 90)"
    )
    await state.set_state(OnboardingStates.SERVICE_DURATION)


@router.callback_query(OnboardingStates.SERVICE_PRICE, F.data == "skip_price")
async def process_service_price_skip(callback: CallbackQuery, state: FSMContext):
    await state.update_data(service_price=None)
    await callback.message.edit_text(
        "Цена: <b>по договорённости</b>\n\n"
        "Укажите <b>длительность в минутах</b> (только число):\n"
        "(например: 30, 60, 90)"
    )
    await state.set_state(OnboardingStates.SERVICE_DURATION)
    await callback.answer()


@router.message(OnboardingStates.SERVICE_DURATION)
async def process_service_duration(message: Message, state: FSMContext):
    try:
        duration = int(message.text.strip())
        if duration < 5 or duration > 480:
            raise ValueError
    except ValueError:
        await message.answer("Введите длительность числом от 5 до 480 минут:")
        return
    await state.update_data(service_duration=duration)
    await message.answer(
        "Отлично! Теперь настроим расписание.\n\n"
        "Выберите <b>рабочие дни</b> (нажимайте на дни, потом «Готово»):",
        reply_markup=schedule_days_kb(),
    )
    await state.set_state(OnboardingStates.SCHEDULE_DAYS)


# ── Шаг 4: Расписание ───────────────────────────────────────────

@router.callback_query(OnboardingStates.SCHEDULE_DAYS, F.data.startswith("day:"))
async def toggle_day(callback: CallbackQuery, state: FSMContext):
    day = int(callback.data.split(":")[1])
    data = await state.get_data()
    selected = set(data.get("selected_days", []))
    if day in selected:
        selected.discard(day)
    else:
        selected.add(day)
    await state.update_data(selected_days=list(selected))
    await callback.message.edit_reply_markup(reply_markup=schedule_days_kb(selected))
    await callback.answer()


@router.callback_query(OnboardingStates.SCHEDULE_DAYS, F.data == "days_done")
async def days_done(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get("selected_days", [])
    if not selected:
        await callback.answer("Выберите хотя бы один рабочий день!", show_alert=True)
        return
    await callback.message.edit_text(
        "Во сколько начинается ваш рабочий день?\n\n"
        "Введите <b>время начала</b> (например: 9:00 или 10:00):"
    )
    await state.set_state(OnboardingStates.SCHEDULE_START)
    await callback.answer()


@router.message(OnboardingStates.SCHEDULE_START)
async def process_schedule_start(message: Message, state: FSMContext):
    time_str = message.text.strip()
    try:
        parts = time_str.replace(".", ":").split(":")
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
    except (ValueError, IndexError):
        await message.answer("Введите время в формате ЧЧ:ММ (например: 9:00):")
        return
    await state.update_data(schedule_start_h=hour, schedule_start_m=minute)
    await message.answer(
        f"Начало: <b>{hour:02d}:{minute:02d}</b>\n\n"
        "Во сколько заканчивается рабочий день?\n"
        "Введите <b>время конца</b> (например: 18:00 или 20:00):"
    )
    await state.set_state(OnboardingStates.SCHEDULE_END)


@router.message(OnboardingStates.SCHEDULE_END)
async def process_schedule_end(message: Message, state: FSMContext):
    time_str = message.text.strip()
    try:
        parts = time_str.replace(".", ":").split(":")
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
    except (ValueError, IndexError):
        await message.answer("Введите время в формате ЧЧ:ММ (например: 18:00):")
        return

    data = await state.get_data()
    start_total = data["schedule_start_h"] * 60 + data["schedule_start_m"]
    end_total = hour * 60 + minute
    if end_total <= start_total:
        await message.answer("Время конца должно быть позже времени начала. Попробуйте ещё раз:")
        return

    await state.update_data(schedule_end_h=hour, schedule_end_m=minute)
    await message.answer(
        f"Конец: <b>{hour:02d}:{minute:02d}</b>\n\n"
        "Выберите <b>шаг записи</b> (длительность одного слота):",
        reply_markup=slot_step_kb(),
    )
    await state.set_state(OnboardingStates.SCHEDULE_STEP)


@router.callback_query(OnboardingStates.SCHEDULE_STEP, F.data.startswith("step:"))
async def process_step(callback: CallbackQuery, state: FSMContext, db: AsyncSession):
    step = int(callback.data.split(":")[1])
    data = await state.get_data()

    telegram_id = callback.from_user.id
    username = callback.from_user.username or f"user_{telegram_id}"

    existing_master_id = data.get("existing_master_id")

    consent_at_str = data.get("consent_at")
    consent_at = datetime.fromisoformat(consent_at_str) if consent_at_str else datetime.utcnow()

    if existing_master_id:
        # Update existing master record
        result = await db.execute(select(Master).where(Master.id == existing_master_id))
        master = result.scalar_one()
        master.username = username
        master.display_name = data["display_name"]
        master.niche = data["niche"]
        master.is_onboarded = True
        master.consent_given = True
        master.consent_at = consent_at
        await db.flush()
    else:
        # Create new master
        referral_code = generate_referral_code()
        now = datetime.utcnow()
        master = Master(
            telegram_id=telegram_id,
            username=username,
            display_name=data["display_name"],
            niche=data["niche"],
            referral_code=referral_code,
            is_onboarded=True,
            consent_given=True,
            consent_at=consent_at,
            subscription_status="trial",
            trial_ends_at=now + timedelta(days=settings.trial_days),
            referrer_id=data.get("referrer_id"),
        )
        db.add(master)
        await db.flush()

    # Create service
    service = Service(
        master_id=master.id,
        name=data["service_name"],
        price=data.get("service_price"),
        duration_min=data["service_duration"],
    )
    db.add(service)

    # Create schedule templates for selected days
    from datetime import time as dt_time

    start_time = dt_time(data["schedule_start_h"], data["schedule_start_m"])
    end_time = dt_time(data["schedule_end_h"], data["schedule_end_m"])

    for day in data["selected_days"]:
        template = ScheduleTemplate(
            master_id=master.id,
            day_of_week=day,
            start_time=start_time,
            end_time=end_time,
            slot_step_min=step,
            is_working=True,
        )
        db.add(template)

    # [DISABLED - referral] Create referral record if came via ref link
    # if not existing_master_id and data.get("referrer_id"):
    #     referral = Referral(
    #         referrer_id=data["referrer_id"],
    #         referred_id=master.id,
    #     )
    #     db.add(referral)

    # Log events
    if not existing_master_id:
        db.add(Event(master_id=master.id, event_type="master_registered"))
        db.add(Event(master_id=master.id, event_type="trial_started"))
        # [DISABLED - referral]
        # if data.get("referrer_id"):
        #     db.add(Event(master_id=master.id, event_type="referral_used", payload={"referrer_id": data["referrer_id"]}))
    db.add(Event(master_id=master.id, event_type="master_onboarded"))

    await db.commit()

    # Build links
    booking_link = f"https://t.me/{settings.bot_username}?start=book_{username}"
    # [DISABLED - referral] ref_link = f"https://t.me/{settings.bot_username}?start=ref_{master.referral_code}"

    await callback.message.edit_text(
        f"🎉 <b>Готово!</b>\n\n"
        f"Ваш профиль настроен.\n\n"
        f"🔗 <b>Ссылка для клиентов</b> (запись):\n"
        f"<code>{booking_link}</code>\n\n"
        f"Отправьте ссылку вашему клиенту! 🚀"
        # [DISABLED - referral] Referral link section removed
    )

    await state.clear()
    await callback.answer()

    # Set personalized menu button so master can open Mini App directly
    await callback.bot.set_chat_menu_button(
        chat_id=callback.from_user.id,
        menu_button=MenuButtonWebApp(
            text="Открыть",
            web_app=WebAppInfo(url=f"{settings.miniapp_url}?master={username}"),
        ),
    )

    # Send main menu
    await callback.message.answer("Вот ваше главное меню:", reply_markup=main_menu_kb())

    # Feedback block + referral nudge
    await callback.message.answer(
        "💬 <b>Нам очень важна ваша обратная связь!</b>\n\n"
        "Если что-то не работает или нужен дополнительный функционал "
        "для вашей работы — напишите нам прямо в этот бот.\n\n"
        "Мы читаем каждое сообщение и активно развиваем продукт 🙏\n\n"
        "— — —\n"
        "Если среди ваших коллег есть те, кому это тоже может помочь — "
        "поделитесь ботом @plotinahelperbot. Будем рады 🤝"
    )


# ── Main menu refresh ────────────────────────────────────────────

@router.message(Command("menu"))
async def cmd_menu(message: Message, master: Master | None):
    if not master or not master.is_onboarded:
        await message.answer("Сначала завершите настройку профиля через /start")
        return
    await message.answer("Главное меню:", reply_markup=main_menu_kb())


# ── Reset onboarding ─────────────────────────────────────────────

@router.message(Command("reset"))
async def cmd_reset(message: Message, state: FSMContext, db: AsyncSession, master: Master | None):
    await state.clear()

    if not master:
        await message.answer("Вы ещё не зарегистрированы. Введите /start для начала.")
        return

    # Delete related data and reset master
    await db.execute(
        ScheduleTemplate.__table__.delete().where(ScheduleTemplate.master_id == master.id)
    )
    await db.execute(
        ScheduleOverride.__table__.delete().where(ScheduleOverride.master_id == master.id)
    )
    await db.execute(
        Service.__table__.delete().where(Service.master_id == master.id)
    )

    master.is_onboarded = False
    master.display_name = None
    master.niche = None
    master.bio = None
    await db.commit()

    await state.update_data(existing_master_id=master.id)
    await message.answer(RESET_CONSENT_TEXT, reply_markup=consent_kb("reset"))
    await state.set_state(OnboardingStates.CONSENT)


# ── Catch unfinished onboarding ──────────────────────────────────

@router.message(StateFilter(OnboardingStates))
async def onboarding_fallback(message: Message, state: FSMContext):
    await message.answer(
        "Вы ещё не завершили настройку профиля.\n"
        "Пожалуйста, ответьте на текущий вопрос или введите /start чтобы начать заново."
    )

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton


def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Услуги"), KeyboardButton(text="📅 Расписание")],
            [KeyboardButton(text="📖 Записи"), KeyboardButton(text="🔗 Моя ссылка")],
            [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="❓ Помощь")],
            [KeyboardButton(text="💬 Обратная связь")],
            # [DISABLED - monetization] KeyboardButton(text="💳 Подписка")
            # [DISABLED - referral] KeyboardButton(text="🎁 Рефералы")
        ],
        resize_keyboard=True,
    )


def niche_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💅 Бьюти", callback_data="niche:beauty"),
                InlineKeyboardButton(text="📚 Репетитор", callback_data="niche:tutor"),
            ],
            [
                InlineKeyboardButton(text="🏋️ Тренер", callback_data="niche:trainer"),
                InlineKeyboardButton(text="🧠 Психолог", callback_data="niche:psychologist"),
            ],
            [
                InlineKeyboardButton(text="📷 Фото", callback_data="niche:photo"),
                InlineKeyboardButton(text="🔧 Другое", callback_data="niche:other"),
            ],
        ]
    )


WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


def schedule_days_kb(selected: set[int] | None = None) -> InlineKeyboardMarkup:
    selected = selected or set()
    buttons = []
    row = []
    for i, day in enumerate(WEEKDAYS):
        mark = "✅" if i in selected else "⬜"
        row.append(InlineKeyboardButton(text=f"{mark} {day}", callback_data=f"day:{i}"))
        if len(row) == 4 or i == len(WEEKDAYS) - 1:
            buttons.append(row)
            row = []
    buttons.append([InlineKeyboardButton(text="✅ Готово — сохранить дни", callback_data="days_done")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def slot_step_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="15 мин", callback_data="step:15"),
                InlineKeyboardButton(text="30 мин", callback_data="step:30"),
                InlineKeyboardButton(text="60 мин", callback_data="step:60"),
            ]
        ]
    )


def confirm_cancel_kb(confirm_data: str, cancel_data: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Принять", callback_data=confirm_data),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=cancel_data),
            ]
        ]
    )


def booking_tabs_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⏳ Ожидают", callback_data="tab:pending"),
                InlineKeyboardButton(text="📅 Сегодня", callback_data="tab:today"),
            ],
            [
                InlineKeyboardButton(text="📆 Предстоящие", callback_data="tab:upcoming"),
                InlineKeyboardButton(text="📋 История", callback_data="tab:history"),
            ],
        ]
    )


def booking_notification_kb(booking_id: int) -> InlineKeyboardMarkup:
    """Keyboard sent to master when new booking arrives."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Принять", callback_data=f"bk_confirm:{booking_id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"bk_reject:{booking_id}"),
            ],
            [
                InlineKeyboardButton(text="💬 Написать клиенту", callback_data=f"bk_msg:{booking_id}"),
            ],
        ]
    )


def cancel_booking_kb(booking_id: int) -> InlineKeyboardMarkup:
    """Cancel button for confirmed bookings (master side)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отменить запись", callback_data=f"bk_cancel:{booking_id}")],
        ]
    )


def client_cancel_kb(booking_id: int) -> InlineKeyboardMarkup:
    """Cancel button shown to client in reminders."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отменить запись", callback_data=f"cl_cancel:{booking_id}")],
        ]
    )


def client_cancel_confirm_kb(booking_id: int) -> InlineKeyboardMarkup:
    """Confirm cancellation by client."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Да, отменить", callback_data=f"cl_cancel_yes:{booking_id}"),
                InlineKeyboardButton(text="Нет, оставить", callback_data=f"cl_cancel_no:{booking_id}"),
            ],
        ]
    )


def client_reply_kb(booking_id: int) -> InlineKeyboardMarkup:
    """Reply button for client when master sends a message."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💬 Ответить", callback_data=f"cl_reply:{booking_id}")],
        ]
    )

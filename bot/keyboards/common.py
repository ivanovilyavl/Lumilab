from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton


def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Услуги"), KeyboardButton(text="📅 Расписание")],
            [KeyboardButton(text="📖 Записи"), KeyboardButton(text="🔗 Моя ссылка")],
            [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="💳 Подписка")],
            [KeyboardButton(text="🎁 Рефералы"), KeyboardButton(text="❓ Помощь")],
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
                InlineKeyboardButton(text="📅 Предстоящие", callback_data="tab:upcoming"),
                InlineKeyboardButton(text="📋 История", callback_data="tab:history"),
            ]
        ]
    )

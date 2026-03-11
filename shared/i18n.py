"""
Internationalisation helper.
Usage:  from shared.i18n import t
        text = t(master.language, "new_booking_master", pseudo=..., ...)
"""

STRINGS: dict[str, dict[str, str]] = {
    # ── Russian ───────────────────────────────────────────────────────────
    "ru": {
        # Language selection
        "lang_select": (
            "🌍 Выберите язык интерфейса и уведомлений:\n"
            "Select interface language / Seleccione el idioma:"
        ),
        "lang_chosen": "🇷🇺 Отлично, работаем на русском!",

        # Onboarding
        "enter_name": (
            "Давайте настроим ваш профиль.\n\n"
            "Как вас называть клиентам?\n"
            "(Можно имя, название студии или любой псевдоним)"
        ),
        "name_error": "Имя должно быть от 2 до 64 символов. Попробуйте ещё раз:",
        "enter_niche": "Отлично, {name}! 👋\n\nВыберите вашу сферу деятельности:",
        "enter_service_name": (
            "Теперь добавим вашу первую услугу.\n\n"
            "Введите <b>название услуги</b>:\n"
            "(например: Стрижка, Маникюр, Урок английского)"
        ),
        "service_name_error": "Название услуги — от 1 до 128 символов. Попробуйте ещё раз:",
        "enter_price": "Услуга: <b>{name}</b>\n\nУкажите <b>цену</b> или пропустите, если цена индивидуальная:",
        "skip_price_btn": "Пропустить (цена по договорённости)",
        "price_error": "Введите цену числом от 0 до 1 000 000:",
        "price_set": "Цена: <b>{price}</b>\n\nУкажите <b>длительность в минутах</b> (только число):\n(например: 30, 60, 90)",
        "price_by_agreement": "по договорённости",
        "price_skipped": "Цена: <b>по договорённости</b>\n\nУкажите <b>длительность в минутах</b> (только число):\n(например: 30, 60, 90)",
        "duration_error": "Введите длительность числом от 5 до 480 минут:",
        "enter_schedule_days": "Отлично! Теперь настроим расписание.\n\nВыберите <b>рабочие дни</b> (нажимайте на дни, потом «Готово»):",
        "schedule_days_error": "Выберите хотя бы один рабочий день!",
        "enter_schedule_start": "Во сколько начинается ваш рабочий день?\n\nВведите <b>время начала</b> (например: 9:00 или 10:00):",
        "schedule_start_error": "Введите время в формате ЧЧ:ММ (например: 9:00):",
        "enter_schedule_end": "Начало: <b>{start}</b>\n\nВо сколько заканчивается рабочий день?\nВведите <b>время конца</b> (например: 18:00 или 20:00):",
        "schedule_end_error": "Введите время в формате ЧЧ:ММ (например: 18:00):",
        "schedule_end_conflict": "Время конца должно быть позже времени начала.",
        "enter_slot_step": "Расписание: <b>{start} – {end}</b>\n\nС каким шагом создавать слоты для записи?",

        # Booking notifications → master
        "new_booking_master": (
            "📅 Новая запись!\n\n"
            "👤 {pseudo}\n"
            "💅 {service} · {duration} мин · {price}\n"
            "📆 {date} в {time}"
        ),
        # Booking notifications → client
        "booking_created_client": (
            "📋 <b>Заявка принята!</b>\n\n"
            "👤 {master}\n"
            "💅 {service} · {duration} мин · {price}\n"
            "📆 {date} в {time}\n\n"
            "⏳ Ожидайте подтверждения от мастера."
        ),
        "booking_confirmed_client": (
            "✅ <b>Ваша запись подтверждена!</b>\n\n"
            "👤 {master}\n"
            "{service_line}"
            "📅 {date} в {time}\n\n"
            "🔔 Мы напомним вам за 24 ч и за 2 ч до визита."
        ),
        "service_line": "💅 {service} · {duration} мин · {price}\n",
        "reminder_24h": (
            "⏰ Напоминание о записи\n\n"
            "👤 {master}\n"
            "💅 {service} · {duration} мин · {price}\n"
            "📆 Завтра в {time}"
        ),
        "reminder_2h": (
            "⏰ Через 2 часа — ваша запись!\n\n"
            "👤 {master} · {service}\n"
            "🕐 Сегодня в {time}"
        ),
        "min_unit": "мин",
        # Currency
        "currency_select": "💱 Выберите валюту для отображения цен на услуги:",
        "currency_chosen": "✅ Валюта сохранена: {label}",
        "currency_label_RUB": "₽ Рубль",
        "currency_label_USD": "$ Доллар",
        "currency_label_EUR": "€ Евро",
    },

    # ── English ───────────────────────────────────────────────────────────
    "en": {
        "lang_select": (
            "🌍 Выберите язык интерфейса и уведомлений:\n"
            "Select interface language / Seleccione el idioma:"
        ),
        "lang_chosen": "🇬🇧 Great, switching to English!",

        "enter_name": (
            "Let's set up your profile.\n\n"
            "What name should clients see?\n"
            "(Your name, studio name, or any alias)"
        ),
        "name_error": "Name must be 2–64 characters. Please try again:",
        "enter_niche": "Great, {name}! 👋\n\nSelect your field of work:",
        "enter_service_name": (
            "Now let's add your first service.\n\n"
            "Enter the <b>service name</b>:\n"
            "(e.g. Haircut, Manicure, English lesson)"
        ),
        "service_name_error": "Service name must be 1–128 characters. Please try again:",
        "enter_price": "Service: <b>{name}</b>\n\nEnter the <b>price</b> or skip if it varies:",
        "skip_price_btn": "Skip (price on request)",
        "price_error": "Enter a number between 0 and 1 000 000:",
        "price_set": "Price: <b>{price}</b>\n\nEnter the <b>duration in minutes</b>:\n(e.g. 30, 60, 90)",
        "price_by_agreement": "price on request",
        "price_skipped": "Price: <b>on request</b>\n\nEnter the <b>duration in minutes</b>:\n(e.g. 30, 60, 90)",
        "duration_error": "Enter a number between 5 and 480 minutes:",
        "enter_schedule_days": "Great! Now let's set up your schedule.\n\nSelect your <b>working days</b> (tap days, then «Done»):",
        "schedule_days_error": "Please select at least one working day!",
        "enter_schedule_start": "What time does your working day start?\n\nEnter <b>start time</b> (e.g. 9:00 or 10:00):",
        "schedule_start_error": "Enter time in HH:MM format (e.g. 9:00):",
        "enter_schedule_end": "Start: <b>{start}</b>\n\nWhat time does your working day end?\nEnter <b>end time</b> (e.g. 18:00 or 20:00):",
        "schedule_end_error": "Enter time in HH:MM format (e.g. 18:00):",
        "schedule_end_conflict": "End time must be later than start time.",
        "enter_slot_step": "Schedule: <b>{start} – {end}</b>\n\nWhat slot interval should be used for bookings?",

        "new_booking_master": (
            "📅 New booking!\n\n"
            "👤 {pseudo}\n"
            "💅 {service} · {duration} min · {price}\n"
            "📆 {date} at {time}"
        ),
        "booking_created_client": (
            "📋 <b>Booking received!</b>\n\n"
            "👤 {master}\n"
            "💅 {service} · {duration} min · {price}\n"
            "📆 {date} at {time}\n\n"
            "⏳ Waiting for confirmation from the specialist."
        ),
        "booking_confirmed_client": (
            "✅ <b>Your booking is confirmed!</b>\n\n"
            "👤 {master}\n"
            "{service_line}"
            "📅 {date} at {time}\n\n"
            "🔔 We'll remind you 24h and 2h before your visit."
        ),
        "service_line": "💅 {service} · {duration} min · {price}\n",
        "reminder_24h": (
            "⏰ Booking reminder\n\n"
            "👤 {master}\n"
            "💅 {service} · {duration} min · {price}\n"
            "📆 Tomorrow at {time}"
        ),
        "reminder_2h": (
            "⏰ Your appointment is in 2 hours!\n\n"
            "👤 {master} · {service}\n"
            "🕐 Today at {time}"
        ),
        "min_unit": "min",
        # Currency
        "currency_select": "💱 Select the currency for displaying service prices:",
        "currency_chosen": "✅ Currency saved: {label}",
        "currency_label_RUB": "₽ Ruble",
        "currency_label_USD": "$ Dollar",
        "currency_label_EUR": "€ Euro",
    },

    # ── Spanish ───────────────────────────────────────────────────────────
    "es": {
        "lang_select": (
            "🌍 Выберите язык интерфейса и уведомлений:\n"
            "Select interface language / Seleccione el idioma:"
        ),
        "lang_chosen": "🇪🇸 ¡Perfecto, cambiando al español!",

        "enter_name": (
            "Configuremos tu perfil.\n\n"
            "¿Cómo deben llamarte tus clientes?\n"
            "(Tu nombre, nombre del estudio o cualquier alias)"
        ),
        "name_error": "El nombre debe tener entre 2 y 64 caracteres. Inténtalo de nuevo:",
        "enter_niche": "¡Genial, {name}! 👋\n\nSelecciona tu área de trabajo:",
        "enter_service_name": (
            "Ahora agreguemos tu primer servicio.\n\n"
            "Introduce el <b>nombre del servicio</b>:\n"
            "(p.ej. Corte de pelo, Manicura, Clase de inglés)"
        ),
        "service_name_error": "El nombre debe tener entre 1 y 128 caracteres. Inténtalo de nuevo:",
        "enter_price": "Servicio: <b>{name}</b>\n\nIntroduce el <b>precio</b> o sáltalo si varía:",
        "skip_price_btn": "Omitir (precio a convenir)",
        "price_error": "Introduce un número entre 0 y 1 000 000:",
        "price_set": "Precio: <b>{price}</b>\n\nIntroduce la <b>duración en minutos</b>:\n(p.ej. 30, 60, 90)",
        "price_by_agreement": "precio a convenir",
        "price_skipped": "Precio: <b>a convenir</b>\n\nIntroduce la <b>duración en minutos</b>:\n(p.ej. 30, 60, 90)",
        "duration_error": "Introduce un número entre 5 y 480 minutos:",
        "enter_schedule_days": "¡Genial! Ahora configuremos el horario.\n\nSelecciona tus <b>días laborables</b> (toca los días y luego «Listo»):",
        "schedule_days_error": "¡Selecciona al menos un día laborable!",
        "enter_schedule_start": "¿A qué hora empieza tu jornada laboral?\n\nIntroduce la <b>hora de inicio</b> (p.ej. 9:00 o 10:00):",
        "schedule_start_error": "Introduce la hora en formato HH:MM (p.ej. 9:00):",
        "enter_schedule_end": "Inicio: <b>{start}</b>\n\n¿A qué hora termina tu jornada laboral?\nIntroduce la <b>hora de fin</b> (p.ej. 18:00 o 20:00):",
        "schedule_end_error": "Introduce la hora en formato HH:MM (p.ej. 18:00):",
        "schedule_end_conflict": "La hora de fin debe ser posterior a la de inicio.",
        "enter_slot_step": "Horario: <b>{start} – {end}</b>\n\n¿Con qué intervalo crear los turnos?",

        "new_booking_master": (
            "📅 ¡Nueva cita!\n\n"
            "👤 {pseudo}\n"
            "💅 {service} · {duration} min · {price}\n"
            "📆 {date} a las {time}"
        ),
        "booking_created_client": (
            "📋 <b>¡Solicitud recibida!</b>\n\n"
            "👤 {master}\n"
            "💅 {service} · {duration} min · {price}\n"
            "📆 {date} a las {time}\n\n"
            "⏳ Esperando confirmación del especialista."
        ),
        "booking_confirmed_client": (
            "✅ <b>¡Tu cita está confirmada!</b>\n\n"
            "👤 {master}\n"
            "{service_line}"
            "📅 {date} a las {time}\n\n"
            "🔔 Te recordaremos 24h y 2h antes de tu visita."
        ),
        "service_line": "💅 {service} · {duration} min · {price}\n",
        "reminder_24h": (
            "⏰ Recordatorio de cita\n\n"
            "👤 {master}\n"
            "💅 {service} · {duration} min · {price}\n"
            "📆 Mañana a las {time}"
        ),
        "reminder_2h": (
            "⏰ ¡Tu cita es en 2 horas!\n\n"
            "👤 {master} · {service}\n"
            "🕐 Hoy a las {time}"
        ),
        "min_unit": "min",
        # Currency
        "currency_select": "💱 Selecciona la moneda para mostrar los precios de los servicios:",
        "currency_chosen": "✅ Moneda guardada: {label}",
        "currency_label_RUB": "₽ Rublo",
        "currency_label_USD": "$ Dólar",
        "currency_label_EUR": "€ Euro",
    },
}

SUPPORTED_LANGS = {"ru", "en", "es"}
LANG_LABELS = {"ru": "🇷🇺 Русский", "en": "🇬🇧 English", "es": "🇪🇸 Español"}

CURRENCY_SYMBOLS: dict[str, str] = {"RUB": "₽", "USD": "$", "EUR": "€"}
SUPPORTED_CURRENCIES = {"RUB", "USD", "EUR"}
CURRENCY_LABELS = {"RUB": "₽ Рубль", "USD": "$ Доллар", "EUR": "€ Евро"}


def currency_symbol(currency: str | None) -> str:
    return CURRENCY_SYMBOLS.get(currency or "RUB", currency or "RUB")


def fmt_price(price: int | None, currency: str | None = "RUB", lang: str | None = "ru") -> str:
    """Format price with currency symbol; returns localised 'by agreement' if price is None."""
    if price is None:
        l = lang if lang in SUPPORTED_LANGS else "ru"
        return STRINGS[l].get("price_by_agreement") or "по договорённости"
    sym = currency_symbol(currency)
    if currency in ("USD", "EUR"):
        return f"{sym}{price}"
    return f"{price} {sym}"


def t(lang: str | None, key: str, **kwargs: object) -> str:
    """Return translated string for the given language, falling back to Russian."""
    l = lang if lang in SUPPORTED_LANGS else "ru"
    text = STRINGS[l].get(key) or STRINGS["ru"].get(key, key)
    return text.format(**kwargs) if kwargs else text

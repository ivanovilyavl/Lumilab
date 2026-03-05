from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command("help"))
@router.message(F.text == "❓ Помощь")
async def cmd_help(message: Message):
    await message.answer(
        "❓ <b>Помощь</b>\n\n"
        "<b>Команды:</b>\n"
        "/start — Начать / перезапустить бота\n"
        "/profile — Ваш профиль\n"
        "/services — Управление услугами\n"
        "/schedule — Расписание\n"
        "/bookings — Журнал записей\n"
        "/mylink — Ссылка для клиентов\n"
        "/referral — Реферальная программа\n"
        "/subscription — Подписка\n"
        "/help — Эта справка\n\n"
        "<b>Как это работает:</b>\n"
        "1. Настройте профиль, услуги и расписание\n"
        "2. Отправьте ссылку клиентам (/mylink)\n"
        "3. Клиент выбирает услугу и время\n"
        "4. Вы получаете уведомление и подтверждаете\n\n"
        "Вопросы? Пишите @zapisbot_support"
    )

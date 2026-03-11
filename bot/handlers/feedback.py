import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from db.models import Master

router = Router()
logger = logging.getLogger(__name__)


class FeedbackStates(StatesGroup):
    WAITING_TEXT = State()


@router.message(Command("feedback"))
@router.message(F.text == "💬 Обратная связь")
async def cmd_feedback(message: Message, state: FSMContext, master: Master | None):
    if not master:
        await message.answer("Сначала зарегистрируйтесь через /start")
        return
    await message.answer(
        "💬 <b>Обратная связь</b>\n\n"
        "Напишите ваше сообщение — постараемся ответить как можно скорее.\n\n"
        "Для отмены введите /cancel"
    )
    await state.set_state(FeedbackStates.WAITING_TEXT)


@router.message(Command("cancel"), FeedbackStates.WAITING_TEXT)
async def cancel_feedback(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено.")


@router.message(FeedbackStates.WAITING_TEXT)
async def process_feedback_text(message: Message, state: FSMContext, master: Master):
    await state.clear()

    text = (message.text or "").strip()
    if not text:
        await message.answer("Пустое сообщение не отправлено. Попробуйте ещё раз.")
        return

    from aiogram import Bot
    from aiogram.client.default import DefaultBotProperties
    from aiogram.enums import ParseMode
    from shared.config import settings

    username = f"@{master.username}" if master.username else f"id:{master.telegram_id}"
    feedback_msg = (
        f"💬 <b>FEEDBACK</b> от {username}\n"
        f"Мастер: {master.display_name or '—'} | Ниша: {master.niche or '—'}\n"
        f"──────────────────\n"
        f"{text}\n"
        f"──────────────────\n"
        f"↩️ Ответьте на это сообщение, чтобы написать мастеру.\n"
        f"[MASTER_TG_ID:{master.telegram_id}]"
    )

    if settings.analytics_bot_token and settings.admin_ids:
        bot = Bot(
            token=settings.analytics_bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        try:
            for admin_id in settings.admin_ids:
                try:
                    await bot.send_message(admin_id, feedback_msg)
                except Exception as e:
                    logger.warning(f"feedback: failed to send to admin {admin_id}: {e}")
        finally:
            await bot.session.close()

    await message.answer("✅ Сообщение отправлено! Мы свяжемся с вами в ближайшее время.")

import logging
import re

from aiogram import Router, F
from aiogram.types import Message

from shared.config import settings

router = Router()
logger = logging.getLogger(__name__)

# Pattern to extract master's telegram_id from a feedback message
_MASTER_TG_ID_RE = re.compile(r"\[MASTER_TG_ID:(\d+)\]")


@router.message(F.reply_to_message)
async def handle_admin_reply(message: Message):
    """When admin replies to a feedback message — forward the reply to the master via main bot."""
    original_text = message.reply_to_message.text or ""
    match = _MASTER_TG_ID_RE.search(original_text)
    if not match:
        # Not a feedback message, ignore
        return

    master_tg_id = int(match.group(1))
    reply_text = (message.text or "").strip()
    if not reply_text:
        await message.reply("Пустой ответ — мастеру ничего не отправлено.")
        return

    from aiogram import Bot
    from aiogram.client.default import DefaultBotProperties
    from aiogram.enums import ParseMode

    main_bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    try:
        await main_bot.send_message(
            master_tg_id,
            f"📩 <b>Ответ от поддержки:</b>\n\n{reply_text}",
        )
        await message.reply("✅ Ответ отправлен мастеру.")
        logger.info(f"handle_admin_reply: sent reply to master tg_id={master_tg_id}")
    except Exception as e:
        logger.warning(f"handle_admin_reply: failed to send to master {master_tg_id}: {e}")
        await message.reply(f"❌ Не удалось отправить мастеру: {e}")
    finally:
        await main_bot.session.close()

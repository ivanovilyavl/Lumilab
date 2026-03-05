from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import func, select, case
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Master

router = Router()

NICHE_LABELS = {
    "beauty": "💅 Бьюти",
    "tutor": "📚 Репетитор",
    "trainer": "🏋️ Тренер",
    "psychologist": "🧠 Психолог",
    "photo": "📷 Фото",
    "other": "🔧 Другое",
}


@router.message(Command("niches"))
async def cmd_niches(message: Message, db: AsyncSession):
    result = await db.execute(
        select(
            Master.niche,
            func.count().label("total"),
            func.count(case((Master.subscription_status == "active", 1))).label("paying"),
        )
        .where(Master.is_onboarded == True)
        .group_by(Master.niche)
        .order_by(func.count().desc())
    )
    rows = result.all()

    lines = ["📊 <b>Распределение по нишам</b>\n"]
    for row in rows:
        label = NICHE_LABELS.get(row.niche, row.niche or "—")
        conv = (row.paying / row.total * 100) if row.total else 0
        lines.append(f"{label}: <b>{row.total}</b> (платят: {row.paying}, конв: {conv:.0f}%)")

    if not rows:
        lines.append("Нет данных")

    await message.answer("\n".join(lines))

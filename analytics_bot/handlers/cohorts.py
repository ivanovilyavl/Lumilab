from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

router = Router()

COHORT_SQL = """
SELECT
    date_trunc('week', m.created_at) AS cohort_week,
    COUNT(*) AS cohort_size,
    COUNT(CASE WHEN EXISTS (
        SELECT 1 FROM events e
        WHERE e.master_id = m.id
          AND e.event_type = 'booking_created'
          AND e.created_at >= m.created_at + INTERVAL '7 days'
          AND e.created_at <  m.created_at + INTERVAL '14 days'
    ) THEN 1 END) AS week_2_retained
FROM masters m
WHERE m.created_at > NOW() - INTERVAL '8 weeks'
GROUP BY 1
ORDER BY 1 DESC
"""


@router.message(Command("cohorts"))
async def cmd_cohorts(message: Message, db: AsyncSession):
    result = await db.execute(text(COHORT_SQL))
    rows = result.all()

    lines = ["📊 <b>Когортный анализ (8 недель)</b>\n"]
    lines.append(f"{'Неделя':<12} {'Размер':>7} {'Ret W2':>7} {'%':>5}")
    lines.append("─" * 35)

    for row in rows:
        week = row.cohort_week.strftime("%d.%m") if row.cohort_week else "—"
        size = row.cohort_size
        retained = row.week_2_retained
        pct = (retained / size * 100) if size else 0
        lines.append(f"{week:<12} {size:>7} {retained:>7} {pct:>4.0f}%")

    if not rows:
        lines.append("Нет данных")

    await message.answer(f"<pre>{chr(10).join(lines)}</pre>")

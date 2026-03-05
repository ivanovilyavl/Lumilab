from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Referral, Master

router = Router()


@router.message(Command("referrals"))
async def cmd_referrals(message: Message, db: AsyncSession):
    # Total referrals
    result = await db.execute(select(func.count()).select_from(Referral))
    total = result.scalar() or 0

    # Applied bonuses
    result = await db.execute(
        select(func.count()).select_from(Referral).where(Referral.bonus_applied == True)
    )
    applied = result.scalar() or 0

    # K-factor: total masters from referrals / total masters
    result = await db.execute(select(func.count()).select_from(Master))
    total_masters = result.scalar() or 1
    k_factor = total / total_masters if total_masters else 0

    # Top 5 referrers
    result = await db.execute(
        select(Referral.referrer_id, func.count().label("cnt"))
        .group_by(Referral.referrer_id)
        .order_by(func.count().desc())
        .limit(5)
    )
    top_referrers = result.all()

    lines = [
        f"🎁 <b>Рефералы</b>\n",
        f"Всего приглашений: <b>{total}</b>",
        f"Бонусов начислено: <b>{applied}</b>",
        f"K-фактор: <b>{k_factor:.2f}</b>\n",
        f"<b>Топ-5 рефереров:</b>",
    ]

    for i, row in enumerate(top_referrers, 1):
        master = await db.get(Master, row.referrer_id)
        name = master.display_name if master else f"ID {row.referrer_id}"
        lines.append(f"  {i}. {name} — {row.cnt} приглашений")

    if not top_referrers:
        lines.append("  (пока нет)")

    await message.answer("\n".join(lines))

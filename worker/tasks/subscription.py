import asyncio
import logging
from datetime import datetime, timedelta

from sqlalchemy import select, and_

from worker.celery_app import app
from db.models import Master, Referral, Event

logger = logging.getLogger(__name__)


def _get_bot():
    from aiogram import Bot
    from aiogram.client.default import DefaultBotProperties
    from aiogram.enums import ParseMode
    from shared.config import settings
    return Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


async def _check_trial_expiry():
    from db.session import async_session

    now = datetime.utcnow()
    tomorrow_start = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_end = tomorrow_start + timedelta(days=1)

    async with async_session() as db:
        result = await db.execute(
            select(Master).where(
                Master.subscription_status == "trial",
                Master.trial_ends_at >= tomorrow_start,
                Master.trial_ends_at < tomorrow_end,
            )
        )
        masters = list(result.scalars().all())

        bot = _get_bot()
        for m in masters:
            try:
                await bot.send_message(
                    m.telegram_id,
                    "⏰ Завтра заканчивается пробный период.\n\n"
                    "Оформите подписку — 199 ₽/мес, чтобы клиенты "
                    "продолжили записываться.",
                )
            except Exception as e:
                logger.warning(f"Failed to notify master {m.id} about trial expiry: {e}")

        await bot.session.close()
        logger.info(f"Trial expiry: notified {len(masters)} masters")


async def _mark_subscription_expired():
    from db.session import async_session

    now = datetime.utcnow()

    async with async_session() as db:
        # Expired trials
        result = await db.execute(
            select(Master).where(
                Master.subscription_status == "trial",
                Master.trial_ends_at < now,
            )
        )
        for m in result.scalars().all():
            m.subscription_status = "expired"
            db.add(Event(master_id=m.id, event_type="subscription_expired", payload={"reason": "trial_ended"}))

        # Expired active subscriptions
        result = await db.execute(
            select(Master).where(
                Master.subscription_status == "active",
                Master.subscription_ends_at < now,
            )
        )
        for m in result.scalars().all():
            m.subscription_status = "expired"
            db.add(Event(master_id=m.id, event_type="subscription_expired", payload={"reason": "subscription_ended"}))

        await db.commit()


async def _apply_referral_bonuses():
    from db.session import async_session
    from shared.config import settings

    async with async_session() as db:
        # Find unapplied referrals where referred master completed onboarding
        result = await db.execute(
            select(Referral)
            .where(Referral.bonus_applied == False)
        )
        referrals = list(result.scalars().all())

        bot = _get_bot()
        applied = 0

        for ref in referrals:
            referred = await db.get(Master, ref.referred_id)
            if not referred or not referred.is_onboarded:
                continue

            referrer = await db.get(Master, ref.referrer_id)
            if not referrer:
                continue

            # Anti-fraud: soft limit warning
            result2 = await db.execute(
                select(Referral).where(
                    Referral.referrer_id == ref.referrer_id,
                    Referral.bonus_applied == True,
                )
            )
            applied_count = len(list(result2.scalars().all()))
            if applied_count > 50:
                db.add(Event(
                    master_id=ref.referrer_id,
                    event_type="referral_limit_warning",
                    payload={"total_referrals": applied_count + 1},
                ))
                logger.warning(f"Master {ref.referrer_id} exceeded 50 referrals")

            referrer.referral_bonus_days += settings.referral_bonus_days
            ref.bonus_applied = True
            applied += 1

            db.add(Event(
                master_id=ref.referrer_id,
                event_type="referral_bonus_applied",
                payload={"referred_id": ref.referred_id, "bonus_days": settings.referral_bonus_days},
            ))

            try:
                await bot.send_message(
                    referrer.telegram_id,
                    f"🎉 Ваш друг {referred.display_name} зарегистрировался!\n"
                    f"+{settings.referral_bonus_days} дней к подписке\n\n"
                    f"Накоплено бонусных дней: {referrer.referral_bonus_days}",
                )
            except Exception as e:
                logger.warning(f"Failed to notify referrer {referrer.id}: {e}")

        await db.commit()
        await bot.session.close()
        logger.info(f"Referral bonuses: {applied} applied")


@app.task(name="worker.tasks.subscription.check_trial_expiry")
def check_trial_expiry():
    asyncio.run(_check_trial_expiry())


@app.task(name="worker.tasks.subscription.mark_subscription_expired")
def mark_subscription_expired():
    asyncio.run(_mark_subscription_expired())


@app.task(name="worker.tasks.subscription.apply_referral_bonuses")
def apply_referral_bonuses():
    asyncio.run(_apply_referral_bonuses())

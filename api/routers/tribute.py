import hashlib
import hmac
from datetime import datetime, timedelta

from fastapi import APIRouter, Header, HTTPException, Request, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db
from db.models import Event, Master, Payment
from shared.config import settings

router = APIRouter(prefix="/api", tags=["tribute"])


class TributeWebhookPayload(BaseModel):
    event: str
    subscriber_id: str
    telegram_user_id: int
    amount: int  # kopecks
    period_start: datetime
    period_end: datetime
    payment_id: str


def verify_tribute_signature(body: bytes, signature: str) -> bool:
    if not settings.tribute_webhook_secret:
        return False
    expected = hmac.new(
        settings.tribute_webhook_secret.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/tribute/webhook")
async def handle_tribute_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_tribute_signature: str = Header(...),
):
    body = await request.body()

    if not verify_tribute_signature(body, x_tribute_signature):
        raise HTTPException(403, "Invalid signature")

    payload = TributeWebhookPayload.model_validate_json(body)

    # Find master
    result = await db.execute(
        select(Master).where(Master.telegram_id == payload.telegram_user_id)
    )
    master = result.scalar_one_or_none()
    if not master:
        raise HTTPException(404, "Master not found")

    if payload.event in ("subscription.activated", "subscription.renewed"):
        master.subscription_status = "active"
        master.subscription_ends_at = payload.period_end
        master.tribute_subscriber_id = payload.subscriber_id

        # Apply accumulated referral bonus days
        if master.referral_bonus_days > 0:
            master.subscription_ends_at += timedelta(days=master.referral_bonus_days)
            master.referral_bonus_days = 0

        # Save payment record
        payment = Payment(
            master_id=master.id,
            tribute_payment_id=payload.payment_id,
            amount_rub=payload.amount // 100,
            status="paid",
            period_start=payload.period_start,
            period_end=payload.period_end,
            raw_webhook=payload.model_dump(mode="json"),
        )
        db.add(payment)

        db.add(Event(
            master_id=master.id,
            event_type="subscription_activated",
            payload={"amount": payload.amount, "payment_id": payload.payment_id},
        ))

    elif payload.event in ("subscription.cancelled", "subscription.expired"):
        master.subscription_status = "expired"
        db.add(Event(master_id=master.id, event_type="subscription_expired"))

    await db.commit()
    return {"status": "ok"}

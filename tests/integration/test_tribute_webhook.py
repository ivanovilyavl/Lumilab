import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone

import pytest

from db.models import Master


@pytest.fixture
async def master_in_db(db_session):
    master = Master(
        telegram_id=777,
        username="tribute_test",
        display_name="Tribute Test",
        niche="other",
        referral_code="TRIBUTE1",
        is_onboarded=True,
        subscription_status="trial",
        trial_ends_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    db_session.add(master)
    await db_session.commit()
    return master


def _sign(body: bytes, secret: str = "test_secret") -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


@pytest.mark.asyncio
async def test_tribute_invalid_signature(api_client):
    body = b'{"event":"test"}'
    response = await api_client.post(
        "/api/tribute/webhook",
        content=body,
        headers={"X-Tribute-Signature": "bad_signature", "Content-Type": "application/json"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_tribute_activation(api_client, master_in_db, monkeypatch):
    # Monkeypatch the secret for testing
    monkeypatch.setattr("shared.config.settings.tribute_webhook_secret", "test_secret")

    now = datetime.now(timezone.utc)
    payload = {
        "event": "subscription.activated",
        "subscriber_id": "sub_123",
        "telegram_user_id": master_in_db.telegram_id,
        "amount": 19900,
        "period_start": now.isoformat(),
        "period_end": (now + timedelta(days=30)).isoformat(),
        "payment_id": "pay_001",
    }
    body = json.dumps(payload).encode()
    signature = _sign(body)

    response = await api_client.post(
        "/api/tribute/webhook",
        content=body,
        headers={"X-Tribute-Signature": signature, "Content-Type": "application/json"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

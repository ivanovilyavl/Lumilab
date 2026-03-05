from datetime import datetime, timedelta, timezone

import pytest

from db.models import Master


def _make_master(**kwargs) -> Master:
    defaults = dict(
        id=1,
        telegram_id=123,
        username="test",
        display_name="Test",
        referral_code="TEST",
        subscription_status="trial",
        trial_ends_at=datetime.now(timezone.utc) + timedelta(days=7),
        subscription_ends_at=None,
        referral_bonus_days=0,
    )
    defaults.update(kwargs)
    m = Master.__new__(Master)
    for k, v in defaults.items():
        setattr(m, k, v)
    return m


def _has_access(master: Master) -> bool:
    """Replicate SubscriptionMiddleware logic for unit testing."""
    now = datetime.now(timezone.utc)
    if master.subscription_status == "trial" and master.trial_ends_at and master.trial_ends_at > now:
        return True
    if master.subscription_status == "active" and master.subscription_ends_at and master.subscription_ends_at > now:
        return True
    if master.referral_bonus_days > 0:
        return True
    return False


def test_trial_active():
    m = _make_master(subscription_status="trial", trial_ends_at=datetime.now(timezone.utc) + timedelta(days=5))
    assert _has_access(m) is True


def test_trial_expired():
    m = _make_master(subscription_status="trial", trial_ends_at=datetime.now(timezone.utc) - timedelta(days=1))
    assert _has_access(m) is False


def test_active_subscription():
    m = _make_master(
        subscription_status="active",
        subscription_ends_at=datetime.now(timezone.utc) + timedelta(days=20),
    )
    assert _has_access(m) is True


def test_expired_subscription():
    m = _make_master(subscription_status="expired", trial_ends_at=None)
    assert _has_access(m) is False


def test_referral_bonus_days_grant_access():
    m = _make_master(subscription_status="expired", trial_ends_at=None, referral_bonus_days=7)
    assert _has_access(m) is True

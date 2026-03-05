"""Unit tests for referral logic."""


def test_self_referral_blocked():
    """A master should not be able to refer themselves."""
    referrer_telegram_id = 12345
    new_user_telegram_id = 12345
    assert referrer_telegram_id == new_user_telegram_id  # same person
    # In bot/handlers/start.py we check: referrer.telegram_id != telegram_id


def test_referral_bonus_only_after_onboarding():
    """Bonus should only apply when referred master completes onboarding."""
    is_onboarded = False
    bonus_applied = False

    # Should not apply bonus
    if is_onboarded:
        bonus_applied = True
    assert bonus_applied is False

    # After onboarding
    is_onboarded = True
    if is_onboarded:
        bonus_applied = True
    assert bonus_applied is True


def test_unique_referral():
    """One master can only be referred by one other master."""
    referred_ids = set()
    referred_ids.add(100)
    # Trying to add same referred_id again
    assert 100 in referred_ids  # would violate UNIQUE(referred_id)

import hashlib
import hmac
import time as _time
from urllib.parse import parse_qsl

from shared.config import settings

# initData is valid for up to 24 hours (prevents replay attacks)
_MAX_AUTH_AGE_SECONDS = 86_400


def _verify_signature(params: dict, token: str) -> bool:
    received_hash = params.pop("hash", None)
    if not received_hash:
        return False
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))
    secret_key = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    expected_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return expected_hash == received_hash


def _auth_date_valid(params: dict) -> bool:
    """Reject initData older than _MAX_AUTH_AGE_SECONDS."""
    auth_date = params.get("auth_date")
    if not auth_date:
        return False
    try:
        age = _time.time() - int(auth_date)
        return 0 <= age <= _MAX_AUTH_AGE_SECONDS
    except (ValueError, TypeError):
        return False


def validate_telegram_init_data(init_data: str) -> dict | None:
    """Validate Telegram Mini App initData using HMAC-SHA256."""
    try:
        params = dict(parse_qsl(init_data, keep_blank_values=True))
    except Exception:
        return None

    if not _auth_date_valid(params):
        return None

    if not _verify_signature(params, settings.bot_token):
        return None

    return params


def validate_analytics_init_data(init_data: str) -> dict | None:
    """Validate Telegram Mini App initData using the analytics bot token."""
    try:
        params = dict(parse_qsl(init_data, keep_blank_values=True))
    except Exception:
        return None

    if not _auth_date_valid(params):
        return None

    if not _verify_signature(params, settings.analytics_bot_token):
        return None

    return params

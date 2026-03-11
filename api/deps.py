import json

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import validate_telegram_init_data
from db.models import Master
from db.session import get_db

__all__ = ["get_db", "get_master_owner"]


async def get_master_owner(
    username: str,
    init_data: str | None,
    db: AsyncSession,
) -> Master:
    """Validate Telegram auth and return master if the caller owns this profile."""
    if not init_data:
        raise HTTPException(401, "Auth required")
    auth_data = validate_telegram_init_data(init_data)
    if not auth_data:
        raise HTTPException(401, "Invalid auth")
    user_str = auth_data.get("user")
    if not user_str:
        raise HTTPException(401, "No user in auth data")
    try:
        user = json.loads(user_str)
        telegram_id = int(user["id"])
    except (ValueError, KeyError):
        raise HTTPException(401, "Invalid user data")

    result = await db.execute(
        select(Master).where(Master.username == username, Master.is_active == True)
    )
    master = result.scalar_one_or_none()
    if not master:
        raise HTTPException(404, "Master not found")
    if master.telegram_id != telegram_id:
        raise HTTPException(403, "Forbidden")
    return master

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db
from db.models import Master, Service

router = APIRouter(prefix="/api", tags=["master"])


class ServiceOut(BaseModel):
    id: int
    name: str
    description: str | None
    price: int
    duration_min: int

    model_config = {"from_attributes": True}


class MasterOut(BaseModel):
    id: int
    username: str
    display_name: str | None
    bio: str | None
    photo_file_id: str | None
    niche: str | None
    accepting_bookings: bool
    services: list[ServiceOut]

    model_config = {"from_attributes": True}


@router.get("/master/{username}", response_model=MasterOut)
async def get_master(username: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Master).where(Master.username == username, Master.is_active == True)
    )
    master = result.scalar_one_or_none()
    if not master:
        raise HTTPException(status_code=404, detail="Master not found")

    result = await db.execute(
        select(Service).where(
            Service.master_id == master.id,
            Service.is_active == True,
        ).order_by(Service.sort_order)
    )
    services = list(result.scalars().all())

    return MasterOut(
        id=master.id,
        username=master.username,
        display_name=master.display_name,
        bio=master.bio,
        photo_file_id=master.photo_file_id,
        niche=master.niche,
        accepting_bookings=master.subscription_status != "expired",
        services=[ServiceOut.model_validate(s) for s in services],
    )

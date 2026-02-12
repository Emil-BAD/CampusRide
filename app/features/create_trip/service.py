from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.location import Building, Dorm
from app.models.trip import Trip


async def get_or_create_user(session: AsyncSession, tg_id: int, username: str | None = None) -> User:
    result = await session.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()
    if user:
        if username is not None and user.username != username:
            user.username = username
        return user
    user = User(tg_id=tg_id, username=username)
    session.add(user)
    await session.flush()
    return user


async def save_trip(
    session: AsyncSession,
    data: dict,
    tg_id: int,
    username: str | None = None,
) -> Trip:
    user = await get_or_create_user(session, tg_id, username)

    dorm_result = await session.execute(select(Dorm).where(Dorm.code == str(data["pointFrom"])))
    dorm = dorm_result.scalar_one()
    building_result = await session.execute(select(Building).where(Building.code == str(data["pointTo"])))
    building = building_result.scalar_one()

    date_obj = datetime.strptime(data["date"], "%Y-%m-%d").date()
    time_obj = datetime.strptime(data["time"], "%H:%M").time()

    trip = Trip(
        creator_id=user.id,
        type_trip=data["typeTrip"],
        point_from_id=dorm.id,
        point_to_id=building.id,
        date=date_obj,
        time=time_obj,
        quantity_places=int(data["quantityPlaces"]),
        comment=data.get("comment") or None,
    )
    session.add(trip)
    await session.flush()
    return trip

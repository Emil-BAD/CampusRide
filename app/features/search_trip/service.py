from datetime import date
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trip import Trip, TripParticipant
from app.models.user import User
from app.models.location import Building, Dorm


async def search_trips(
    session: AsyncSession,
    dorm_code: str | None,
    building_code: str | None,
    filter_date: date | None = None,
    exclude_creator_tg_id: int | None = None,
) -> list[dict]:
    """Поиск активных поездок. filter_date — фильтр по дню, exclude_creator_tg_id — не показывать поездки этого пользователя."""
    today = date.today()
    q = (
        select(Trip)
        .where(
            and_(
                Trip.status == "active",
                Trip.date >= today,
            )
        )
        .options(selectinload(Trip.point_from), selectinload(Trip.point_to), selectinload(Trip.participants), selectinload(Trip.creator))
        .order_by(Trip.date, Trip.time)
    )
    if dorm_code:
        dorm = (await session.execute(select(Dorm).where(Dorm.code == dorm_code))).scalar_one_or_none()
        if dorm:
            q = q.where(Trip.point_from_id == dorm.id)
    if building_code:
        bld = (await session.execute(select(Building).where(Building.code == building_code))).scalar_one_or_none()
        if bld:
            q = q.where(Trip.point_to_id == bld.id)
    if filter_date:
        q = q.where(Trip.date == filter_date)

    result = await session.execute(q)
    trips = result.scalars().all()

    out = []
    for t in trips:
        places_left = t.quantity_places - len(t.participants)
        if places_left <= 0:
            continue
        if exclude_creator_tg_id and t.creator and t.creator.tg_id == exclude_creator_tg_id:
            continue
        short = f"Общ.{t.point_from.code} → Зд.{t.point_to.code}, {t.date.strftime('%d.%m')} {t.time.strftime('%H:%M')}"
        out.append({
            "id": t.id,
            "short": short,
            "trip": t,
        })
    return out


async def join_trip(
    session: AsyncSession,
    trip_id: int,
    user_db_id: int,
) -> tuple[bool, str, int | None]:
    """
    Добавляет пользователя в поездку. Возвращает (success, message, creator_tg_id|None).
    При успехе: создаёт TripParticipant, заполняется одно место.
    """
    result = await session.execute(
        select(Trip).where(Trip.id == trip_id).options(selectinload(Trip.participants), selectinload(Trip.creator))
    )
    trip = result.scalar_one_or_none()
    if not trip:
        return False, "Поездка не найдена.", None
    if trip.status != "active":
        return False, "Поездка уже завершена или отменена.", None
    if trip.date < date.today():
        return False, "Поездка уже прошла.", None
    places_left = trip.quantity_places - len(trip.participants)
    if places_left <= 0:
        return False, "В поездке нет свободных мест.", None

    exists = (
        await session.execute(
            select(TripParticipant).where(
                TripParticipant.trip_id == trip_id,
                TripParticipant.user_id == user_db_id,
            )
        )
    ).scalar_one_or_none()
    if exists:
        return False, "Вы уже в этой поездке.", None
    if trip.creator_id == user_db_id:
        return False, "Вы не можете присоединиться к своей поездке.", None

    part = TripParticipant(trip_id=trip_id, user_id=user_db_id)
    session.add(part)
    await session.flush()
    creator_tg_id = trip.creator.tg_id if trip.creator else None
    return True, "success", creator_tg_id

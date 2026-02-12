from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trip import Trip, TripParticipant
from app.models.user import User


async def get_my_trips(
    session: AsyncSession,
    tg_id: int,
    active: bool,
) -> tuple[list[Trip], int | None]:
    """Поездки пользователя: active=True — активные (date>=today), active=False — прошедшие."""
    user = (await session.execute(select(User).where(User.tg_id == tg_id))).scalar_one_or_none()
    if not user:
        return [], None

    created_ids = (await session.execute(select(Trip.id).where(Trip.creator_id == user.id))).scalars().all()
    participated_ids = (
        await session.execute(select(TripParticipant.trip_id).where(TripParticipant.user_id == user.id))
    ).scalars().all()
    trip_ids = list(set(created_ids) | set(participated_ids))
    if not trip_ids:
        return [], user.id

    q = (
        select(Trip)
        .where(Trip.id.in_(trip_ids))
        .options(selectinload(Trip.point_from), selectinload(Trip.point_to), selectinload(Trip.creator), selectinload(Trip.participants))
        .order_by(Trip.date.desc(), Trip.time.desc())
    )
    result = await session.execute(q)
    trips = result.scalars().unique().all()
    today = date.today()

    if active:
        return [t for t in trips if t.date >= today and t.status == "active"], user.id
    return [t for t in trips if t.date < today or t.status != "active"], user.id


async def cancel_trip(
    session: AsyncSession,
    trip_id: int,
    creator_user_id: int,
) -> tuple[bool, str, list[int], float]:
    """
    Отменяет поездку (status=cancelled). Только создатель может отменить.
    Возвращает (success, message, participant_tg_ids, penalty_applied).
    """
    result = await session.execute(
        select(Trip)
        .where(Trip.id == trip_id)
        .options(selectinload(Trip.participants).joinedload(TripParticipant.user), selectinload(Trip.creator))
    )
    trip = result.scalar_one_or_none()
    if not trip:
        return False, "Поездка не найдена.", [], 0.0
    if trip.creator_id != creator_user_id:
        return False, "Только создатель может удалить поездку.", [], 0.0
    if trip.status != "active":
        return False, "Поездка уже отменена или завершена.", [], 0.0

    participant_tg_ids = [p.user.tg_id for p in trip.participants if p.user]
    penalty_applied = 0.0
    trip.status = "cancelled"
    await session.flush()

    # Штраф организатору: -0.25 за каждого участника, если отмена менее чем за час
    if participant_tg_ids:
        trip_dt = datetime.combine(trip.date, trip.time)
        if (trip_dt - datetime.now()) > timedelta(0) and (trip_dt - datetime.now()) < timedelta(hours=1):
            penalty = Decimal("0.25") * len(participant_tg_ids)
            penalty_applied = float(penalty)
            creator = trip.creator
            if creator:
                creator.rating = max(Decimal("0"), (creator.rating or Decimal("5")) - penalty)
    await session.flush()
    return True, "ok", participant_tg_ids, penalty_applied


async def leave_trip(
    session: AsyncSession,
    trip_id: int,
    user_db_id: int,
) -> tuple[bool, str, int | None, bool]:
    """
    Пассажир выходит из поездки. Возвращает (success, message, creator_tg_id|None, penalty_applied).
    Если выход менее чем за час — штраф -0.5 рейтинга.
    """
    result = await session.execute(
        select(Trip)
        .where(Trip.id == trip_id)
        .options(selectinload(Trip.creator), selectinload(Trip.participants))
    )
    trip = result.scalar_one_or_none()
    if not trip:
        return False, "Поездка не найдена.", None, False
    if trip.creator_id == user_db_id:
        return False, "Организатор не может выйти из поездки. Используйте удаление.", None, False
    if trip.status != "active":
        return False, "Поездка уже отменена или завершена.", None, False

    part = (
        await session.execute(
            select(TripParticipant).where(
                TripParticipant.trip_id == trip_id,
                TripParticipant.user_id == user_db_id,
            )
        )
    ).scalar_one_or_none()
    if not part:
        return False, "Вы не в этой поездке.", None, False

    creator_tg_id = trip.creator.tg_id if trip.creator else None
    trip_dt = datetime.combine(trip.date, trip.time)
    penalty_applied = False
    if (trip_dt - datetime.now()) < timedelta(hours=1) and (trip_dt - datetime.now()) > timedelta(0):
        penalty_applied = True
        user = (await session.execute(select(User).where(User.id == user_db_id))).scalar_one()
        user.rating = max(Decimal("0"), (user.rating or Decimal("5")) - Decimal("0.5"))

    await session.delete(part)
    await session.flush()
    return True, "ok", creator_tg_id, penalty_applied

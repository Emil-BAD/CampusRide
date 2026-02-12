"""
Заполнение справочников buildings и dorms из constants.
Запускать после init_db.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.location import Building, Dorm
from app.constants import BUILDINGS, DORMS


async def seed_locations(session: AsyncSession) -> None:
    """Добавляет buildings и dorms, если таблицы пусты."""
    n_buildings = (await session.execute(select(func.count()).select_from(Building))).scalar()
    if n_buildings == 0:
        buildings = [
            Building(code=code, address=addr)
            for code, addr in BUILDINGS.items()
        ]
        session.add_all(buildings)

    n_dorms = (await session.execute(select(func.count()).select_from(Dorm))).scalar()
    if n_dorms == 0:
        dorms = [
            Dorm(code=code, address=addr)
            for code, addr in DORMS.items()
        ]
        session.add_all(dorms)

    await session.commit()

import os
import asyncio
from datetime import date, datetime

from aiogram.fsm.storage.redis import RedisStorage
from aiogram.client.default import DefaultBotProperties
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload

from app.core.redis import redis_client
from app.routers import setup_routers
from app.database import AsyncSessionLocal
from app.models.trip import Trip, TripParticipant
from app.reminders import get_moscow_now, send_15m_reminder, send_5m_reminder


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="create", description="Создать поездку"),
        BotCommand(command="search", description="Найти поездку"),
        BotCommand(command="help", description="Помощь по боту"),
        BotCommand(command="profile", description="Мой профиль"),
        BotCommand(command="stop_chat", description="Выйти из чата поездки"),
    ]
    await bot.set_my_commands(commands)


bot = Bot(
    token=os.getenv("BOT_TOKEN"),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher(storage=RedisStorage(redis_client))

setup_routers(dp)


async def reminders_worker():
    """Фоновый воркер: напоминания за 15 и 5 минут до поездки. Время — Москва (UTC+3)."""
    while True:
        now = get_moscow_now()
        today = now.date()
        async with AsyncSessionLocal() as session:
            res = await session.execute(
                select(Trip)
                .where(Trip.status == "active", Trip.date >= today)
                .options(
                    selectinload(Trip.creator),
                    selectinload(Trip.participants).joinedload(TripParticipant.user),
                )
            )
            trips = res.scalars().all()

        for trip in trips:
            trip_dt = datetime.combine(trip.date, trip.time)
            delta = (trip_dt - now).total_seconds()
            if delta <= 0:
                continue

            # 15 минут
            if 0 < delta <= 15 * 60:
                key15 = f"trip:{trip.id}:rem15"
                if not await redis_client.get(key15):
                    await send_15m_reminder(bot, trip)
                    await redis_client.setex(key15, 60 * 60, "1")

            # 5 минут
            if 0 < delta <= 5 * 60:
                key5 = f"trip:{trip.id}:rem5"
                if not await redis_client.get(key5):
                    await send_5m_reminder(bot, trip)
                    await redis_client.setex(key5, 60 * 60, "1")

        await asyncio.sleep(60)


async def start_bot():
    await set_commands(bot)
    # фоновые напоминания о поездках
    asyncio.create_task(reminders_worker())
    await dp.start_polling(bot)

"""Напоминания о поездках — московское время (UTC+3)."""
from datetime import datetime, timedelta, timezone

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.models.trip import Trip

# Московское время: UTC+3
MOSCOW_OFFSET_HOURS = 3


def get_moscow_now() -> datetime:
    """Текущее время в Москве (naive datetime)."""
    utc = datetime.now(timezone.utc)
    moscow = utc + timedelta(hours=MOSCOW_OFFSET_HOURS)
    return moscow.replace(tzinfo=None)


async def send_15m_reminder(bot: Bot, trip: Trip) -> None:
    """Отправить напоминание за 15 минут всем (организатор + пассажиры)."""
    trip_dt = datetime.combine(trip.date, trip.time)
    text = (
        f"⏰ Напоминание: поездка #{trip.id} начнётся через 15 минут.\n"
        f"{trip_dt.strftime('%d.%m.%Y %H:%M')}"
    )
    if trip.creator and trip.creator.tg_id:
        await bot.send_message(trip.creator.tg_id, text)
    for p in trip.participants:
        if p.user and p.user.tg_id:
            await bot.send_message(p.user.tg_id, text)


async def send_5m_reminder(bot: Bot, trip: Trip) -> None:
    """Напоминание за 5 минут + кнопка завершения/отмены — только организатору."""
    trip_dt = datetime.combine(trip.date, trip.time)
    text = (
        f"⏰ Поездка #{trip.id} начнётся менее чем через 5 минут.\n"
        f"{trip_dt.strftime('%d.%m.%Y %H:%M')}\n\n"
        "Когда поездка завершится или будет отменена — нажмите одну из кнопок ниже, "
        "чтобы завершить поездку и пройти небольшой опрос."
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Поездка завершена",
                    callback_data=f"trip_done_{trip.id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отменить поездку",
                    callback_data=f"trip_delete_{trip.id}",
                )
            ],
        ]
    )
    if trip.creator and trip.creator.tg_id:
        await bot.send_message(trip.creator.tg_id, text, reply_markup=kb)


async def maybe_send_trip_reminders(bot: Bot, redis_client, trip: Trip) -> None:
    """
    Если поездка начинается менее чем через 15 минут — сразу отправить напоминания.
    Если менее чем через 5 минут — также отправить 5‑минутное с кнопками.
    Время считается по Москве (UTC+3).
    """
    now = get_moscow_now()
    trip_dt = datetime.combine(trip.date, trip.time)
    delta = (trip_dt - now).total_seconds()

    if delta <= 0:
        return

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

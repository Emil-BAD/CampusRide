import html
import textwrap
from datetime import date

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select, func

from app.database import AsyncSessionLocal
from app.features.create_trip.keyboards import start_keyboard
from app.features.create_trip.service import get_or_create_user
from app.models.user import User
from app.models.trip import Trip, TripParticipant


router = Router()


def _format_profile(user: User, created: int, joined: int, active_count: int) -> str:
    rating = float(user.rating or 5.0)
    rating_str = f"{rating:.2f}"
    created_at = user.created_at.date() if user.created_at else date.today()
    created_at_str = created_at.strftime("%d.%m.%Y")

    return textwrap.dedent(
        f"""<b>👤 Мой профиль</b>

<b>Имя:</b> {html.escape(user.username or '') or '—'}
<b>Telegram ID:</b> <code>{user.tg_id}</code>

<b>⭐ Рейтинг:</b> {rating_str} / 5.00

<b>📊 Статистика поездок</b>
• Создано поездок: <b>{created}</b>
• Участие в поездках: <b>{joined}</b>
• Активных поездок сейчас: <b>{active_count}</b>

<b>📅 В сервисе с:</b> {created_at_str}
"""
    )


async def _load_profile_text(tg_id: int) -> str:
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, tg_id, None)
        await session.flush()

        # Созданные поездки
        created_q = await session.execute(
            select(func.count(Trip.id)).where(Trip.creator_id == user.id)
        )
        created_count = created_q.scalar() or 0

        # Участие как пассажир
        joined_q = await session.execute(
            select(func.count(TripParticipant.id)).where(
                TripParticipant.user_id == user.id
            )
        )
        joined_count = joined_q.scalar() or 0

        # Активные поездки (где он создатель или участник)
        today = date.today()
        active_created_q = await session.execute(
            select(func.count(Trip.id)).where(
                Trip.creator_id == user.id,
                Trip.status == "active",
                Trip.date >= today,
            )
        )
        active_created = active_created_q.scalar() or 0

        active_joined_q = await session.execute(
            select(func.count(Trip.id))
            .join(TripParticipant, TripParticipant.trip_id == Trip.id)
            .where(
                TripParticipant.user_id == user.id,
                Trip.status == "active",
                Trip.date >= today,
            )
        )
        active_joined = active_joined_q.scalar() or 0

        active_total = active_created + active_joined

        return _format_profile(user, created_count, joined_count, active_total)


@router.callback_query(F.data == "profile")
async def profile_callback(callback: CallbackQuery):
    tg_id = callback.from_user.id if callback.from_user else 0
    text = await _load_profile_text(tg_id)
    await callback.message.edit_text(text, reply_markup=start_keyboard)
    await callback.answer()


@router.message(Command("profile"))
async def profile_command(message: Message):
    tg_id = message.from_user.id if message.from_user else 0
    text = await _load_profile_text(tg_id)
    await message.answer(text, reply_markup=start_keyboard)


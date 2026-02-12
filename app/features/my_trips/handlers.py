import textwrap
import html
from datetime import datetime
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command

from app.features.create_trip.keyboards import start_keyboard
from app.features.create_trip.service import get_or_create_user
from app.features.my_trips.keyboards import (
    my_trips_menu_kb,
    my_trips_back_kb,
    my_trips_active_kb,
    my_trips_past_kb,
    PER_PAGE,
)
from app.features.my_trips.service import get_my_trips, cancel_trip, leave_trip
from app.database import AsyncSessionLocal
from app.constants import WEEKDAYS_RU, MONTHS_RU, BUILDINGS, DORMS
from app.states.Chat import Chat
from app.models.trip import Trip, TripParticipant
from app.models.user import User
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload

router = Router()


def _start_text(name: str) -> str:
    return textwrap.dedent(
        f"""<b>👋 Привет, {name}!</b>
Добро пожаловать в KAIRide — сервис для совместных поездок студентов общежитий 🚙

Выберите действие ниже 👇"""
    )


def _format_trip_full(t, is_creator: bool = False, num: int = 1) -> str:
    dorm_key = t.point_from.code
    building_key = t.point_to.code
    from_addr = DORMS.get(dorm_key, t.point_from.address)
    to_addr = BUILDINGS.get(building_key, t.point_to.address)
    places_left = t.quantity_places - len(t.participants)
    transport = "Такси" if t.type_trip == "taxi_ts" else "Личный транспорт"
    formatted_date = f"{WEEKDAYS_RU[t.date.weekday()]}, {t.date.day} {MONTHS_RU[t.date.month]} {t.date.year}"
    role = "Организатор" if is_creator else "Участник"
    return (
        f"<b>Поездка {num}</b>\n\n"
        f"<b>📍 Маршрут</b>\n"
        f"   Откуда: {html.escape(from_addr)}\n"
        f"   Куда: {html.escape(to_addr)}\n\n"
        f"<b>📅 Дата и время</b>\n"
        f"   {formatted_date} в {t.time.strftime('%H:%M')}\n\n"
        f"<b>🚗 Детали</b>\n"
        f"   {transport} • Свободно мест: {places_left} • {role}\n\n"
        f"<b>💬 Комментарий</b>\n"
        f"   {html.escape(t.comment or 'Нет')}\n"
    )


@router.callback_query(F.data == "my_trips")
async def my_trips_menu(callback: CallbackQuery):
    text = "🚗 Мои поездки\n\nВыберите раздел:"
    await callback.message.edit_text(text, reply_markup=my_trips_menu_kb())
    await callback.answer()


def _render_my_trips_page(trips: list, user_id: int | None, page: int, title: str, active: bool) -> tuple[str, object]:
    if not trips:
        return f"{title}\n\nУ вас нет поездок.", my_trips_back_kb()
    total_pages = (len(trips) + PER_PAGE - 1) // PER_PAGE
    start = page * PER_PAGE
    chunk = trips[start : start + PER_PAGE]
    lines = []
    for i, t in enumerate(chunk):
        num = start + i + 1
        is_creator = user_id is not None and t.creator_id == user_id
        lines.append(_format_trip_full(t, is_creator, num))
    header = f"{title} (страница {page + 1} из {total_pages})\n\n"
    text = header + "\n\n───\n\n".join(lines)
    if active and user_id is not None:
        kb = my_trips_active_kb(trips, page, user_id)
    elif not active:
        kb = my_trips_past_kb(trips, page)
    else:
        kb = my_trips_back_kb()
    return text, kb


@router.callback_query(F.data == "my_trips_active")
async def my_trips_active(callback: CallbackQuery):
    tg_id = callback.from_user.id if callback.from_user else 0
    async with AsyncSessionLocal() as session:
        trips, user_id = await get_my_trips(session, tg_id, active=True)
    text, kb = _render_my_trips_page(trips, user_id, 0, "🟢 Активные поездки", active=True)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("my_trips_active_p"))
async def my_trips_active_page(callback: CallbackQuery):
    page = int(callback.data.replace("my_trips_active_p", ""))
    tg_id = callback.from_user.id if callback.from_user else 0
    async with AsyncSessionLocal() as session:
        trips, user_id = await get_my_trips(session, tg_id, active=True)
    text, kb = _render_my_trips_page(trips, user_id, page, "🟢 Активные поездки", active=True)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "my_trips_past")
async def my_trips_past(callback: CallbackQuery):
    tg_id = callback.from_user.id if callback.from_user else 0
    async with AsyncSessionLocal() as session:
        trips, user_id = await get_my_trips(session, tg_id, active=False)
    text, kb = _render_my_trips_page(trips, user_id, 0, "🔴 Прошедшие поездки", active=False)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("my_trips_past_p"))
async def my_trips_past_page(callback: CallbackQuery):
    page = int(callback.data.replace("my_trips_past_p", ""))
    tg_id = callback.from_user.id if callback.from_user else 0
    async with AsyncSessionLocal() as session:
        trips, user_id = await get_my_trips(session, tg_id, active=False)
    text, kb = _render_my_trips_page(trips, user_id, page, "🔴 Прошедшие поездки", active=False)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("trip_leave_"))
async def trip_leave(callback: CallbackQuery):
    trip_id = int(callback.data.replace("trip_leave_", ""))
    tg_id = callback.from_user.id if callback.from_user else 0

    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, tg_id, callback.from_user.username if callback.from_user else None)
        await session.flush()
        ok, msg, creator_tg_id, penalty_applied = await leave_trip(session, trip_id, user.id)
        if ok:
            await session.commit()
            if creator_tg_id:
                leaver_name = html.escape(getattr(callback.from_user, "full_name", "") or "Пассажир")
                try:
                    await callback.bot.send_message(
                        creator_tg_id,
                        f"👋 {leaver_name} вышел из вашей поездки.",
                    )
                except Exception:
                    pass
            full_name = getattr(callback.from_user, "full_name", "") or ""
            name_escaped = html.escape(full_name)
            text = "✅ Вы вышли из поездки."
            if penalty_applied:
                text += "\n⚠️ С рейтинга снято 0.5 (выход менее чем за час до поездки)."
            text += "\n\n" + _start_text(name_escaped)
            await callback.message.edit_text(text, reply_markup=start_keyboard)
        else:
            await callback.answer(msg, show_alert=True)
            return
    await callback.answer()


@router.callback_query(F.data.startswith("trip_delete_"))
async def trip_delete(callback: CallbackQuery):
    trip_id = int(callback.data.replace("trip_delete_", ""))
    tg_id = callback.from_user.id if callback.from_user else 0

    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, tg_id, callback.from_user.username if callback.from_user else None)
        await session.flush()
        ok, msg, participant_tg_ids, penalty_applied = await cancel_trip(session, trip_id, user.id)
        if ok:
            await session.commit()
            for pid in participant_tg_ids:
                try:
                    await callback.bot.send_message(
                        pid,
                        "❌ Поездка, к которой вы присоединились, была отменена организатором.",
                    )
                except Exception:
                    pass
            full_name = getattr(callback.from_user, "full_name", "") or ""
            name_escaped = html.escape(full_name)
            text = "✅ Поездка удалена."
            if penalty_applied > 0:
                text += f"\n⚠️ С рейтинга снято {penalty_applied:.2f} (отмена менее чем за час при наличии участников)."
            text += "\n\n" + _start_text(name_escaped)
            await callback.message.edit_text(text, reply_markup=start_keyboard)
        else:
            await callback.answer(msg, show_alert=True)
            return
    await callback.answer()


@router.callback_query(F.data.startswith("trip_chat_"))
async def trip_chat_start(callback: CallbackQuery, state):
    """Вход в режим чата по конкретной поездке."""
    trip_id = int(callback.data.replace("trip_chat_", ""))
    tg_id = callback.from_user.id if callback.from_user else 0

    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(
            session, tg_id, callback.from_user.username if callback.from_user else None
        )
        await session.flush()
        # проверяем, что пользователь — создатель или участник
        res = await session.execute(
            select(Trip)
            .where(Trip.id == trip_id)
            .options(
                selectinload(Trip.participants),
            )
        )
        trip = res.scalar_one_or_none()
        if not trip:
            await callback.answer("Поездка не найдена.", show_alert=True)
            return
        is_creator = trip.creator_id == user.id
        is_participant = any(p.user_id == user.id for p in trip.participants)
        if not (is_creator or is_participant):
            await callback.answer("Вы не связаны с этой поездкой.", show_alert=True)
            return

    await state.set_state(Chat.in_trip)
    await state.update_data(chat_trip_id=trip_id)
    await callback.message.edit_text(
        "💬 Режим чата по поездке включён.\n\n"
        "Отправьте сообщение — его увидят участники поездки.\n"
        "Чтобы выйти из чата, отправьте команду /stop_chat.",
        reply_markup=my_trips_back_kb(),
    )
    await callback.answer()


@router.message(Chat.in_trip)
async def chat_message(message: Message, state):
    """Пересылка сообщений всем остальным участникам поездки."""
    data = await state.get_data()
    trip_id = data.get("chat_trip_id")
    if not trip_id:
        await message.answer(
            "Состояние чата потеряно. Откройте чат ещё раз через 'Мои поездки'."
        )
        await state.clear()
        return
    tg_id = message.from_user.id if message.from_user else 0

    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(
            session, tg_id, message.from_user.username if message.from_user else None
        )
        await session.flush()
        res = await session.execute(
            select(Trip)
            .where(Trip.id == trip_id)
            .options(
                selectinload(Trip.creator),
                selectinload(Trip.participants).joinedload(TripParticipant.user),
            )
        )
        trip = res.scalar_one_or_none()
        if not trip:
            await message.answer("Поездка не найдена или была удалена.")
            await state.clear()
            return

        recipients = []
        # создатель
        if trip.creator and trip.creator.tg_id and trip.creator.tg_id != tg_id:
            recipients.append(trip.creator.tg_id)
        # пассажиры
        for p in trip.participants:
            if p.user and p.user.tg_id and p.user.tg_id != tg_id:
                recipients.append(p.user.tg_id)

        if not recipients:
            await message.answer("Нет других участников, которым можно отправить сообщение.")
            return

        sender_name = html.escape(
            getattr(message.from_user, "full_name", "") or "Пользователь"
        )
        role = "Организатор" if trip.creator_id == user.id else "Пассажир"
        header = (
            f"💬 Сообщение в поездке #{trip.id}\n"
            f"От: <b>{sender_name}</b> ({role})\n\n"
        )
        text = header + html.escape(message.text or "")

        for rid in recipients:
            try:
                await message.bot.send_message(rid, text)
            except Exception:
                continue

        await message.answer("Сообщение отправлено участникам поездки.")


@router.message(Command("stop_chat"))
async def stop_chat(message: Message, state):
    await state.clear()
    full_name = getattr(message.from_user, "full_name", "") or ""
    name_escaped = html.escape(full_name)
    text = "❌ Чат закрыт.\n\n" + _start_text(name_escaped)
    await message.answer(text, reply_markup=start_keyboard)


@router.callback_query(F.data.startswith("chat_share_username_"))
async def chat_share_username(callback: CallbackQuery):
    """Пассажир делится своим @username с организатором конкретной поездки."""
    trip_id = int(callback.data.replace("chat_share_username_", ""))
    tg_id = callback.from_user.id if callback.from_user else 0
    username = callback.from_user.username if callback.from_user else None

    if not username:
        await callback.answer(
            "У вас не указан @username в Telegram. Установите его в настройках аккаунта.",
            show_alert=True,
        )
        return

    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, tg_id, username)
        await session.flush()
        res = await session.execute(
            select(Trip)
            .where(Trip.id == trip_id)
            .options(
                selectinload(Trip.creator),
                selectinload(Trip.participants),
            )
        )
        trip = res.scalar_one_or_none()
        if not trip:
            await callback.answer("Поездка не найдена.", show_alert=True)
            return

        is_creator = trip.creator_id == user.id
        is_participant = any(p.user_id == user.id for p in trip.participants)
        if is_creator:
            await callback.answer(
                "Вы организатор этой поездки — показывать username самому себе не нужно.",
                show_alert=True,
            )
            return
        if not is_participant:
            await callback.answer("Вы не участник этой поездки.", show_alert=True)
            return

        if not trip.creator or not trip.creator.tg_id:
            await callback.answer("Не удалось найти организатора в Telegram.", show_alert=True)
            return

        passenger_name = html.escape(
            getattr(callback.from_user, "full_name", "") or "Пассажир"
        )
        text = (
            f"🙋 Пассажир <b>{passenger_name}</b> поделился своим username для связи по поездке #{trip.id}.\n"
            f"Его Telegram: @{username}"
        )
        try:
            await callback.bot.send_message(trip.creator.tg_id, text)
        except Exception:
            pass

    await callback.answer("Ваш @username отправлен организатору.", show_alert=True)


@router.callback_query(F.data == "my_trips_back")
async def my_trips_back(callback: CallbackQuery):
    full_name = getattr(callback.from_user, "full_name", "") or ""
    name_escaped = html.escape(full_name)
    text = _start_text(name_escaped)
    await callback.message.edit_text(text, reply_markup=start_keyboard)
    await callback.answer()

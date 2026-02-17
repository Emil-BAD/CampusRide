import textwrap
import html
from datetime import datetime
from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from app.features.create_trip.keyboards import start_keyboard
from app.features.search_trip.keyboards import (
    search_filter_dorm_kb,
    search_filter_building_kb,
    search_filter_day_kb,
    trip_list_kb,
    no_trips_back_kb,
)
from app.features.search_trip.states import SearchTrip
from app.features.search_trip.service import search_trips, join_trip
from app.features.create_trip.service import get_or_create_user
from app.database import AsyncSessionLocal
from app.constants import BUILDINGS, DORMS

router = Router()


def _start_text(name: str) -> str:
    return textwrap.dedent(f"""<b>👋 Привет, {name}!</b>
Добро пожаловать в KAIRide — сервис для совместных поездок студентов общежитий 🚙

Выберите действие ниже 👇""")


PER_PAGE = 3


def _format_trip_no_creator(trip_dict: dict, num: int) -> str:
    t = trip_dict["trip"]
    dorm_key = t.point_from.code
    building_key = t.point_to.code
    from_addr = DORMS.get(dorm_key, t.point_from.address)
    to_addr = BUILDINGS.get(building_key, t.point_to.address)
    places_left = t.quantity_places - len(t.participants)
    transport = "Такси" if t.type_trip == "taxi_ts" else "Личный транспорт"
    date_str = t.date.strftime("%d.%m.%Y")
    time_str = t.time.strftime("%H:%M")
    return (
        f"<b>Поездка {num}</b>\n\n"
        f"<b>📍 Маршрут</b>\n"
        f"   Откуда: {html.escape(from_addr)}\n"
        f"   Куда: {html.escape(to_addr)}\n\n"
        f"<b>📅 Дата и время</b>\n"
        f"   {date_str} в {time_str}\n\n"
        f"<b>🚗 Детали</b>\n"
        f"   {transport} • Свободно мест: {places_left}\n\n"
        f"<b>💬 Комментарий</b>\n"
        f"   {html.escape(t.comment or 'Нет')}\n"
    )


@router.message(Command("search"))
async def cmd_search(message: Message, state: FSMContext):
    """Команда /search — старт режима поиска поездок."""
    await state.clear()
    text = "🔍 Выберите общежитие (откуда едете):"
    await message.answer(text, reply_markup=search_filter_dorm_kb())
    await state.set_state(SearchTrip.filter_dorm)


@router.callback_query(F.data == "search_trip")
async def search_trip_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    text = "🔍 Выберите общежитие (откуда едете):"
    await callback.message.edit_text(text, reply_markup=search_filter_dorm_kb())
    await state.set_state(SearchTrip.filter_dorm)
    await callback.answer()


@router.callback_query(SearchTrip.filter_dorm, F.data.startswith("search_dorm"))
async def search_filter_dorm(callback: CallbackQuery, state: FSMContext):
    raw = callback.data.replace("search_dorm", "")
    dorm_code = None if raw == "_any" else raw
    await state.update_data(dorm_code=dorm_code)
    text = "🔍 Выберите учебное здание (пункт назначения):"
    await callback.message.edit_text(text, reply_markup=search_filter_building_kb())
    await state.set_state(SearchTrip.filter_building)
    await callback.answer()


@router.callback_query(SearchTrip.filter_building, F.data.startswith("search_building"))
async def search_filter_building(callback: CallbackQuery, state: FSMContext):
    raw = callback.data.replace("search_building", "")
    building_code = None if raw == "_any" else raw
    await state.update_data(building_code=building_code)
    text = "🔍 Выберите день поездки:"
    await callback.message.edit_text(text, reply_markup=search_filter_day_kb())
    await state.set_state(SearchTrip.filter_day)
    await callback.answer()


@router.callback_query(SearchTrip.filter_day, F.data.startswith("search_day_"))
async def search_filter_day(callback: CallbackQuery, state: FSMContext):
    raw = callback.data.replace("search_day_", "")
    if raw == "any":
        filter_date = None
    else:
        filter_date = datetime.strptime(raw, "%Y-%m-%d").date()

    await state.update_data(filter_date=filter_date.isoformat() if filter_date else None)
    data = await state.get_data()
    dorm_code = data.get("dorm_code")
    building_code = data.get("building_code")
    fd = data.get("filter_date")
    filter_date_val = datetime.strptime(fd, "%Y-%m-%d").date() if fd else None
    tg_id = callback.from_user.id if callback.from_user else 0

    async with AsyncSessionLocal() as session:
        trips = await search_trips(session, dorm_code, building_code, filter_date=filter_date_val, exclude_creator_tg_id=tg_id)

    if not trips:
        text = "😕 По вашему запросу поездок не найдено."
        await callback.message.edit_text(text, reply_markup=no_trips_back_kb())
    else:
        page = 0
        total_pages = (len(trips) + PER_PAGE - 1) // PER_PAGE
        start = page * PER_PAGE
        chunk = trips[start : start + PER_PAGE]
        header = f"🔍 Найдено поездок: {len(trips)} (страница {page + 1} из {total_pages})\n\n"
        body = "\n\n───\n\n".join(_format_trip_no_creator(t, start + i + 1) for i, t in enumerate(chunk))
        text = header + body
        await callback.message.edit_text(text, reply_markup=trip_list_kb(trips, page))
    await state.set_state(SearchTrip.select_trip)
    await callback.answer()


@router.callback_query(SearchTrip.select_trip, F.data.startswith("search_page_"))
async def search_page(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.replace("search_page_", ""))
    data = await state.get_data()
    dorm_code = data.get("dorm_code")
    building_code = data.get("building_code")
    fd = data.get("filter_date")
    filter_date = datetime.strptime(fd, "%Y-%m-%d").date() if fd else None
    tg_id = callback.from_user.id if callback.from_user else 0

    async with AsyncSessionLocal() as session:
        trips = await search_trips(session, dorm_code, building_code, filter_date=filter_date, exclude_creator_tg_id=tg_id)

    if not trips:
        text = "😕 По вашему запросу поездок не найдено."
        await callback.message.edit_text(text, reply_markup=no_trips_back_kb())
    else:
        total_pages = (len(trips) + PER_PAGE - 1) // PER_PAGE
        start = page * PER_PAGE
        chunk = trips[start : start + PER_PAGE]
        header = f"🔍 Найдено поездок: {len(trips)} (страница {page + 1} из {total_pages})\n\n"
        body = "\n\n───\n\n".join(_format_trip_no_creator(t, start + i + 1) for i, t in enumerate(chunk))
        text = header + body
        await callback.message.edit_text(text, reply_markup=trip_list_kb(trips, page))
    await callback.answer()


@router.callback_query(SearchTrip.select_trip, F.data.startswith("trip_join_"))
async def trip_join(callback: CallbackQuery, state: FSMContext):
    trip_id = int(callback.data.replace("trip_join_", ""))
    tg_id = callback.from_user.id if callback.from_user else 0
    username = callback.from_user.username if callback.from_user else None

    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, tg_id, username)
        await session.flush()
        ok, msg, creator_tg_id = await join_trip(session, trip_id, user.id)
        if ok:
            await session.commit()

            if creator_tg_id:
                joiner_name = html.escape(getattr(callback.from_user, "full_name", "") or "Пользователь")
                notify_text = f"🔔 К вашей поездке присоединился {joiner_name}."
                try:
                    await callback.bot.send_message(creator_tg_id, notify_text)
                except Exception:
                    pass
        else:
            await callback.answer(msg, show_alert=True)
            return

    await state.clear()
    full_name = getattr(callback.from_user, "full_name", "") or ""
    name_escaped = html.escape(full_name)
    text = "✅ Вы присоединились к поездке!\n\n" + _start_text(name_escaped)
    await callback.message.edit_text(text, reply_markup=start_keyboard)
    await callback.answer()


@router.callback_query(F.data == "cancel_search_trip")
async def cancel_search_trip(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    full_name = getattr(callback.from_user, "full_name", "") or ""
    name_escaped = html.escape(full_name)
    text = _start_text(name_escaped)
    await callback.message.edit_text(text, reply_markup=start_keyboard)
    await callback.answer()

from datetime import datetime, timedelta
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

WEEKDAYS_RU = {
    0: "Пн", 1: "Вт", 2: "Ср", 3: "Чт", 4: "Пт", 5: "Сб", 6: "Вс",
}


def search_filter_dorm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Любое", callback_data="search_dorm_any")],
        [
            InlineKeyboardButton(text="№1", callback_data="search_dorm1"),
            InlineKeyboardButton(text="№2", callback_data="search_dorm2"),
            InlineKeyboardButton(text="№3", callback_data="search_dorm3"),
        ],
        [
            InlineKeyboardButton(text="№4", callback_data="search_dorm4"),
            InlineKeyboardButton(text="№5", callback_data="search_dorm5"),
            InlineKeyboardButton(text="№6", callback_data="search_dorm6"),
        ],
        [
            InlineKeyboardButton(text="№7", callback_data="search_dorm7"),
            InlineKeyboardButton(text="№8", callback_data="search_dorm8"),
        ],
        [InlineKeyboardButton(text="Отменить", callback_data="cancel_search_trip")],
    ])


def search_filter_building_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Любое", callback_data="search_building_any")],
        [
            InlineKeyboardButton(text="№1", callback_data="search_building1"),
            InlineKeyboardButton(text="№2", callback_data="search_building2"),
            InlineKeyboardButton(text="№3", callback_data="search_building3"),
        ],
        [
            InlineKeyboardButton(text="№4", callback_data="search_building4"),
            InlineKeyboardButton(text="№5", callback_data="search_building5"),
            InlineKeyboardButton(text="№6", callback_data="search_building6"),
        ],
        [
            InlineKeyboardButton(text="№7", callback_data="search_building7"),
            InlineKeyboardButton(text="№8", callback_data="search_building8"),
        ],
        [InlineKeyboardButton(text="Отменить", callback_data="cancel_search_trip")],
    ])


def search_filter_day_kb() -> InlineKeyboardMarkup:
    today = datetime.today()
    days = [today + timedelta(days=i) for i in range(7)]
    keyboard = []
    for i in range(0, 7, 2):
        row = []
        for day in days[i : i + 2]:
            row.append(
                InlineKeyboardButton(
                    text=f"{WEEKDAYS_RU[day.weekday()]} {day.strftime('%d.%m')}",
                    callback_data=f"search_day_{day.strftime('%Y-%m-%d')}"
                )
            )
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton(text="Любой день", callback_data="search_day_any")])
    keyboard.append([InlineKeyboardButton(text="Отменить", callback_data="cancel_search_trip")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def trip_list_kb(trips: list, page: int = 0, per_page: int = 3) -> InlineKeyboardMarkup:
    """Клавиатура со списком поездок. Каждая — кнопка «Присоединиться» с trip_join_{id}."""
    start = page * per_page
    chunk = trips[start : start + per_page]
    buttons = []
    for i, t in enumerate(chunk):
        num = start + i + 1
        buttons.append([InlineKeyboardButton(text=f"📍 {num}. {t['short']} — Присоединиться", callback_data=f"trip_join_{t['id']}")])
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅ Назад", callback_data=f"search_page_{page - 1}"))
    if start + per_page < len(trips):
        nav.append(InlineKeyboardButton(text="Вперёд ➡", callback_data=f"search_page_{page + 1}"))
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton(text="Отменить", callback_data="cancel_search_trip")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def no_trips_back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="← К главному меню", callback_data="cancel_search_trip")],
    ])

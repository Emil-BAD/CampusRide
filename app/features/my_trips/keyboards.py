from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

PER_PAGE = 3


def my_trips_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🟢 Активные", callback_data="my_trips_active")],
            [InlineKeyboardButton(text="🔴 Прошедшие", callback_data="my_trips_past")],
            [InlineKeyboardButton(text="← Назад", callback_data="my_trips_back")],
        ]
    )


def my_trips_back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="← К главному меню", callback_data="my_trips_back")],
        ]
    )


def my_trips_active_kb(trips: list, page: int, user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для активных поездок:
    - для создателя: удалить, чат
    - для пассажира: выйти, чат, показать username
    """
    start = page * PER_PAGE
    chunk = trips[start : start + PER_PAGE]
    buttons = []
    for i, t in enumerate(chunk):
        num = start + i + 1
        row_main = []
        if t.creator_id == user_id:
            row_main.append(
                InlineKeyboardButton(
                    text=f"🗑 Удалить поездку {num}", callback_data=f"trip_delete_{t.id}"
                )
            )
        else:
            row_main.append(
                InlineKeyboardButton(
                    text=f"🚪 Выйти из поездки {num}", callback_data=f"trip_leave_{t.id}"
                )
            )
        buttons.append(row_main)

        # Общий чат по поездке
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"💬 Чат по поездке {num}", callback_data=f"trip_chat_{t.id}"
                ),
                # Кнопка показа username — имеет смысл только для пассажира
                *(
                    [
                        InlineKeyboardButton(
                            text=f"🙋 Показать @username {num}",
                            callback_data=f"chat_share_username_{t.id}",
                        )
                    ]
                    if t.creator_id != user_id
                    else []
                ),
            ]
        )
    nav = []
    total_pages = (len(trips) + PER_PAGE - 1) // PER_PAGE
    if page > 0:
        nav.append(
            InlineKeyboardButton(
                text="⬅ Назад", callback_data=f"my_trips_active_p{page - 1}"
            )
        )
    if start + PER_PAGE < len(trips):
        nav.append(
            InlineKeyboardButton(
                text="Вперёд ➡", callback_data=f"my_trips_active_p{page + 1}"
            )
        )
    if nav:
        buttons.append(nav)
    buttons.append(
        [InlineKeyboardButton(text="← К главному меню", callback_data="my_trips_back")]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def my_trips_past_kb(trips: list, page: int) -> InlineKeyboardMarkup:
    """Клавиатура для прошедших поездок (только пагинация)."""
    start = page * PER_PAGE
    nav = []
    total_pages = max(1, (len(trips) + PER_PAGE - 1) // PER_PAGE)
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅ Назад", callback_data=f"my_trips_past_p{page - 1}"))
    if start + PER_PAGE < len(trips):
        nav.append(InlineKeyboardButton(text="Вперёд ➡", callback_data=f"my_trips_past_p{page + 1}"))
    buttons = []
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton(text="← К главному меню", callback_data="my_trips_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

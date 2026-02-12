from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

start_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Создать поездку", callback_data="create_trip")],
        [InlineKeyboardButton(text="Найти поездку", callback_data="search_trip")],
        [InlineKeyboardButton(text="Мои поездки", callback_data="my_trips")],
        [InlineKeyboardButton(text="Мой профиль", callback_data="profile")],
        [InlineKeyboardButton(text="Помощь", callback_data="support")]
    ]
)
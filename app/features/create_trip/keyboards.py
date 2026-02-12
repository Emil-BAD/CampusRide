from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta


start_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Создать поездку", callback_data="create_trip")],
        [InlineKeyboardButton(text="Найти поездку", callback_data="search_trip")],
        [InlineKeyboardButton(text="Мои поездки", callback_data="my_trips")],
        [InlineKeyboardButton(text="Мой профиль", callback_data="profile")],
        [InlineKeyboardButton(text="Помощь", callback_data="support")]
    ]
)

chosse_ts = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Личный транспорт",
                callback_data="personal_ts"
            ),
            InlineKeyboardButton(
                text="Такси",
                callback_data="taxi_ts"
            )
        ]
    ]
)

chosse_fromP = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="№1",
                callback_data="dorm1"
            ),
            InlineKeyboardButton(
                text="№2",
                callback_data="dorm2"
            ),
            InlineKeyboardButton(
                text="№3",
                callback_data="dorm3"
            )
        ],
        [
            InlineKeyboardButton(
                text="№4",
                callback_data="dorm4"
            ),
            InlineKeyboardButton(
                text="№5",
                callback_data="dorm5"
            ),
            InlineKeyboardButton(
                text="№6",
                callback_data="dorm6"
            )
        ],
        [
            InlineKeyboardButton(
                text="№7",
                callback_data="dorm7"
            ),
            InlineKeyboardButton(
                text="№8",
                callback_data="dorm8"
            )
        ],
        [
            InlineKeyboardButton(
                text="Отменить",
                callback_data="cancel_create_trip"
            )
        ]
    ]
)

chosse_toP = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="№1",
                callback_data="building1"
            ),
            InlineKeyboardButton(
                text="№2",
                callback_data="building2"
            ),
            InlineKeyboardButton(
                text="№3",
                callback_data="building3"
            )
        ],
        [
            InlineKeyboardButton(
                text="№4",
                callback_data="building4"
            ),
            InlineKeyboardButton(
                text="№5",
                callback_data="building5"
            ),
            InlineKeyboardButton(
                text="№6",
                callback_data="building6"
            )
        ],
        [
            InlineKeyboardButton(
                text="№7",
                callback_data="building7"
            ),
            InlineKeyboardButton(
                text="№8",
                callback_data="building8"
            )
        ],
        [
            InlineKeyboardButton(
                text="Отменить",
                callback_data="cancel_create_trip"
            )
        ]
    ]
)

WEEKDAYS_RU = {
    0: "Пн",
    1: "Вт",
    2: "Ср",
    3: "Чт",
    4: "Пт",
    5: "Сб",
    6: "Вс",
}


def choose_day_kb():
    today = datetime.today()
    days = [today + timedelta(days=i) for i in range(7)]

    keyboard = []

    for i in range(0, 7, 2):
        row = []
        for day in days[i:i + 2]:
            row.append(
                InlineKeyboardButton(
                    text=f"{WEEKDAYS_RU[day.weekday()]} {day.strftime('%d.%m')}",
                    callback_data=f"day_{day.strftime('%Y-%m-%d')}"
                )
            )
        keyboard.append(row)

    keyboard.append([
        InlineKeyboardButton(
            text="Отменить",
            callback_data="cancel_create_trip"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

only_cancel = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Отменить",
                callback_data="cancel_create_trip"
            )
        ]
    ]
)

places_personal = InlineKeyboardMarkup(
    inline_keyboard=[
        [
          InlineKeyboardButton(
                text="1",
                callback_data="place1"
            ),
          InlineKeyboardButton(
                text="2",
                callback_data="place2"
            ),
          InlineKeyboardButton(
                text="3",
                callback_data="place3"
            )  
        ],
        [
         InlineKeyboardButton(
                text="4",
                callback_data="place3"
            )   
        ],
        [
            InlineKeyboardButton(
                text="Отменить",
                callback_data="cancel_create_trip"
            )
        ]
    ]
)

places_taxi = InlineKeyboardMarkup(
    inline_keyboard=[
        [
          InlineKeyboardButton(
                text="1",
                callback_data="place1"
            ),
          InlineKeyboardButton(
                text="2",
                callback_data="place2"
            ),
          InlineKeyboardButton(
                text="3",
                callback_data="place3"
            )  
        ],
        [
            InlineKeyboardButton(
                text="Отменить",
                callback_data="cancel_create_trip"
            )
        ]
    ]
)

for_comment = InlineKeyboardMarkup(
    inline_keyboard=[
        [
          InlineKeyboardButton(
                text="Пропустить",
                callback_data="pass_com"
            )
        ],
        [
            InlineKeyboardButton(
                text="Отменить",
                callback_data="cancel_create_trip"
            )
        ]
    ]
)

confirm_create_trip = InlineKeyboardMarkup(
    inline_keyboard=[
        [
          InlineKeyboardButton(
                text="Подтвердить",
                callback_data="confirm_trip"
            )
        ],
        [
            InlineKeyboardButton(
                text="Изменить",
                callback_data="change_create_trip"
            )
        ],
        [
            InlineKeyboardButton(
                text="Отмена",
                callback_data="cancel_create_trip"
            )
        ]
    ]
)

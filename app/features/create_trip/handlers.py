from datetime import datetime
from aiogram import F
import re
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from dotenv import load_dotenv
import textwrap
import html
from app.features.create_trip.keyboards import start_keyboard, chosse_ts, chosse_fromP, chosse_toP, choose_day_kb, places_personal, places_taxi, for_comment, confirm_create_trip
from aiogram.fsm.context import FSMContext
from app.states.CreateTrip import CreateTrip
from app.constants import WEEKDAYS_RU, MONTHS_RU, BUILDINGS, DORMS
from aiogram import Router

router = Router()

TIME_PATTERN = r"(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]"

# load environment variables from project .env (so running `python app/main.py` works locally)
load_dotenv()

@router.message(Command("start"))    
async def cmd_start(message: Message):
    full_name = getattr(message.from_user, "full_name", "") or ""
    name_escaped = html.escape(full_name)

    text = textwrap.dedent(f"""<b>👋 Привет, {name_escaped}!</b>
Добро пожаловать в KAIRide — сервис для совместных поездок студентов общежитий 🚙

Выберите действие ниже 👇""")
    await message.answer(text, reply_markup=start_keyboard)

@router.callback_query(F.data == "create_trip")
async def create_trip(callback: CallbackQuery, state: FSMContext):
    #иницилизация класса/функции создания поездки (заполнение данных)
    text = textwrap.dedent(f"""🚗 Отлично! Давайте создадим новую поездку.
Выберите тип поездки 👇""")
    await callback.message.answer(text=text, reply_markup=chosse_ts)
    await state.set_state(CreateTrip.typeTrip)

@router.callback_query(CreateTrip.typeTrip, F.data.in_(["personal_ts", "taxi_ts"]))
async def choose_trip_type(callback: CallbackQuery, state: FSMContext):
    await state.update_data(typeTrip=callback.data)

    await callback.message.answer("📍 От какго общежития выезжаем?", reply_markup=chosse_fromP)
    await state.set_state(CreateTrip.pointFrom)

@router.callback_query(CreateTrip.pointFrom, F.data.in_(["dorm1", "dorm2", "dorm3", "dorm4", "dorm5", "dorm6", "dorm7", "dorm8"]))
async def choose_pointF(callback: CallbackQuery, state: FSMContext):
    dorm_id = callback.data[-1:]
    await state.update_data(pointFrom=dorm_id)
    
    await callback.message.answer("📍 Выберите номер учебного здания КАИ (пункт назначения)?", reply_markup=chosse_toP)
    await state.set_state(CreateTrip.pointTo)

@router.callback_query(
    CreateTrip.pointTo,
    F.data.startswith("building")
)
async def choose_pointTo(callback: CallbackQuery, state: FSMContext):
    building_id = callback.data.replace("building", "")
    
    await state.update_data(pointTo=building_id)

    await callback.message.answer(
        "📍 Выберите день отправления",
        reply_markup=choose_day_kb()
    )
    await state.set_state(CreateTrip.date)

@router.callback_query(CreateTrip.date, lambda c: c.data.startswith("day_"))
async def choose_date(callback: CallbackQuery, state: FSMContext):
    date_value = callback.data.replace("day_", "")
    await state.update_data(date=date_value)
    
    await callback.message.answer("📍 Введите время отправления (в формате HH:MM)\nПример: 09:45")
    await state.set_state(CreateTrip.time)

@router.message(CreateTrip.time)
async def input_time(message: Message, state: FSMContext):
    if not re.fullmatch(TIME_PATTERN, message.text):
        await message.answer(
            "❌ Неверный формат.\n"
            "Введите время в формате HH:MM (например 07:30)"
        )
        return
    await state.update_data(time=message.text)
    data = await state.get_data()
    await message.answer("Сколько мест доступно для пассажиров?", reply_markup=places_taxi if data.get("typeTrip") == "taxi_ts" else places_personal)
    await state.set_state(CreateTrip.quantityPlaces)

@router.callback_query(CreateTrip.quantityPlaces, F.data.in_([f"place{i}" for i in range(1, 5)]))
async def choose_places(callback: CallbackQuery, state: FSMContext):
    places = callback.data.replace("place", "")
    await state.update_data(quantityPlaces=places)
    
    await callback.message.answer("Добавьте коментарий к поездке (необязательно)\nНапример место, время сбора или марка личный машны", reply_markup=for_comment)
    await state.set_state(CreateTrip.comment)

@router.message(CreateTrip.comment)
async def input_comment(message: Message, state: FSMContext):
    await state.update_data(comment=message.text)
    
    await message.answer("Коментарий добавлен")
    await confirm_step(message, state)

@router.callback_query(CreateTrip.comment, F.data == "pass_com")
async def skip_comment(callback: CallbackQuery, state: FSMContext):
    await state.update_data(comment="")
    await callback.message.edit_text("Комментарий пропущен")
    await confirm_step(callback.message, state)
    await callback.answer()

async def confirm_step(message: Message, state: FSMContext):
    data = await state.get_data()

    date_obj = datetime.strptime(data.get("date"), "%Y-%m-%d")

    formatted_date = (
        f"{WEEKDAYS_RU[date_obj.weekday()]}, "
        f"{date_obj.day} {MONTHS_RU[date_obj.month]} {date_obj.year}"
    )

    dorm_key = str(data.get("pointFrom"))
    building_key = str(data.get("pointTo"))

    text = textwrap.dedent(f"""\
        ✅ Проверьте данные поездки:

        • Отправление: {DORMS.get(dorm_key, "Не указано")}
        • Назначение: {BUILDINGS.get(building_key, "Не указано")}
        • Дата: {formatted_date}
        • Время: {data.get("time")}
        • Мест: {data.get("quantityPlaces")}
        • Комментарий: {data.get("comment") or "Нет"}
        • Тип транспорта: {"Такси" if data.get("typeTrip") == "taxi_ts" else "Личный транспорт"}

        Всё верно?
    """)

    await message.answer(text)

@router.callback_query(CreateTrip.confirm, F.data=="confirm_trip")
async def confirm_trip(callback: CallbackQuery, state: FSMContext):
    text = textwrap.dedent(f"""🎉 Поездка успешно создана!
    Теперь другие студенты могут присоединиться.
    🔔 Вы получите уведомление, когда кто-то запишется.

💡 Когда группа участников будет набрана — вызовите такси самостоятельно через любое приложение (Яндекс Go, Uber, Citymobil).
После вызова такси отправьте в чат поездки:
• Скриншот заказа
• Марку и номер автомобиля
• Примерное время прибытия""")
    await callback.message.answer(text=text)

@router.callback_query(CreateTrip.confirm, F.data=="change_create_trip")
async def confirm_trip(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    #изменение поездки
    await callback.message.answer("Измненение поездки...")

@router.callback_query(F.data == "cancel_create_trip")
async def cancel_create_trip(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()

    if current_state is None:
        await callback.answer("Нечего отменять", show_alert=True)
        return

    await state.clear()  # очищаем состояние полностью

    await callback.message.edit_text(
        "❌ Создание поездки отменено.",
    )

    await callback.answer()
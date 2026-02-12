from aiogram import Bot, Dispatcher, F
import re
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
import os
from dotenv import load_dotenv
import textwrap
import html
import asyncio
from app.keyboards.start_board import start_keyboard
from app.keyboards.create_trip_board import chosse_ts, chosse_fromP, chosse_toP, choose_day_kb, places_personal, places_taxi, for_comment, confirm_create_trip
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from app.states.CreateTrip import CreateTrip
from app.core.redis import redis_client

TIME_PATTERN = r"(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]"

# load environment variables from project .env (so running `python app/main.py` works locally)
load_dotenv()

bot = Bot(token=os.getenv('BOT_TOKEN'),
          default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=RedisStorage(redis_client))

@dp.message(Command("start"))    
async def cmd_start(message: Message):
    full_name = getattr(message.from_user, "full_name", "") or ""
    name_escaped = html.escape(full_name)

    text = textwrap.dedent(f"""<b>👋 Привет, {name_escaped}!</b>
Добро пожаловать в KAIRide — сервис для совместных поездок студентов общежитий 🚙

Выберите действие ниже 👇""")
    await message.answer(text, reply_markup=start_keyboard)

@dp.callback_query(F.data == "create_trip")
async def create_trip(callback: CallbackQuery, state: FSMContext):
    #иницилизация класса/функции создания поездки (заполнение данных)
    text = textwrap.dedent(f"""🚗 Отлично! Давайте создадим новую поездку.
Выберите тип поездки 👇""")
    await callback.message.answer(text=text, reply_markup=chosse_ts)
    await state.set_state(CreateTrip.typeTrip)

@dp.callback_query(CreateTrip.typeTrip, F.data.in_(["personal_ts", "taxi_ts"]))
async def choose_trip_type(callback: CallbackQuery, state: FSMContext):
    await state.update_data(typeTrip=callback.data)

    await callback.message.answer("📍 От какго общежития выезжаем?", reply_markup=chosse_fromP)
    await state.set_state(CreateTrip.pointFrom)

@dp.callback_query(CreateTrip.pointFrom, F.data.in_(["dorm1", "dorm2", "dorm3", "dorm4", "dorm5", "dorm6", "dorm7", "dorm8", "cancel_create_trip"]))
async def choose_pointF(callback: CallbackQuery, state: FSMContext):
    await state.update_data(pointFrom=callback.data)
    
    await callback.message.answer("📍 Выберите номер учебного здания КАИ (пункт назначения)?", reply_markup=chosse_toP)
    await state.set_state(CreateTrip.pointTo)

@dp.callback_query(CreateTrip.pointTo, F.data.in_(["building1", "building2", "building3", "building4", "building5", "building6", "building7", "building8", "cancel_create_trip"]))
async def choose_pointTo(callback: CallbackQuery, state: FSMContext):
    await state.update_data(pointTo=callback.data)
    
    await callback.message.answer("📍 Выберете день отправления", reply_markup=choose_day_kb())
    await state.set_state(CreateTrip.date)

@dp.callback_query(CreateTrip.date, lambda c: c.data.startswith("day_"))
async def choose_date(callback: CallbackQuery, state: FSMContext):
    await state.update_data(date=callback.data)
    
    await callback.message.answer("📍 Введите время отправления (в формате HH:MM)\nПример: 09:45")
    await state.set_state(CreateTrip.time)

@dp.message(CreateTrip.time)
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

@dp.callback_query(CreateTrip.quantityPlaces, F.data.in_([f"place{i}" for i in range(1, 5)]))
async def choose_places(callback: CallbackQuery, state: FSMContext):
    await state.update_data(quantityPlaces=callback.data)
    
    await callback.message.answer("Добавьте коментарий к поездке (необязательно)\nНапример место, время сбора или марка личный машны", reply_markup=for_comment)
    await state.set_state(CreateTrip.comment)

@dp.message(CreateTrip.comment)
async def input_comment(message: Message, state: FSMContext):
    await state.update_data(comment=message.text)
    
    await message.answer("Коментарий добавлен")
    await confirm_step(message, state)

@dp.callback_query(CreateTrip.comment, F.data == "pass_com")
async def skip_comment(callback: CallbackQuery, state: FSMContext):
    await state.update_data(comment="")
    await callback.message.edit_text("Комментарий пропущен")
    await confirm_step(callback.message, state)
    await callback.answer()

async def confirm_step(message: Message, state: FSMContext):
    data = await state.get_data()
    
    text = textwrap.dedent(f"""✅ Проверьте данные поездки:
• Отправление: Общежитие {str(data.get("pointFrom"))[-1:]}
• Назначение: Учебное здание КАИ {str(data.get("pointTo"))[-1:]}
• Дата: {str(data.get("date"))}
• Время: {str(data.get("time"))[-5:]}
• Мест: {str(data.get("quantityPlaces"))[-1:]}
• Коментарий: {str(data.get("comment"))} 
• Тип транспорта: {"такси" if data.get("typeTrip") == "taxi_ts" else "личный транспорт"}

Всё верно?""")
    
    await message.answer(text=text, reply_markup=confirm_create_trip)
    await state.set_state(CreateTrip.confirm)

@dp.callback_query(CreateTrip.confirm, F.data=="confirm_trip")
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

@dp.callback_query(CreateTrip.confirm, F.data=="change_create_trip")
async def confirm_trip(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    #изменение поездки
    await callback.message.answer("Измненение поездки...")

@dp.callback_query(F.data == "cancel_create_trip")
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
    
    
    

    
    
    

async def start_bot():
    await dp.start_polling(bot)
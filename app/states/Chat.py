from aiogram.fsm.state import StatesGroup, State


class Chat(StatesGroup):
    in_trip = State()


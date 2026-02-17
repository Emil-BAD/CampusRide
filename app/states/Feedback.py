from aiogram.fsm.state import StatesGroup, State


class Feedback(StatesGroup):
    organizer = State()
    passenger = State()


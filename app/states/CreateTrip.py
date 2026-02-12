from aiogram.fsm.state import StatesGroup, State

class CreateTrip(StatesGroup):
    typeTrip = State()
    pointFrom = State()
    pointTo = State()
    date = State()
    time = State()
    quantityPlaces = State()
    comment = State()
    confirm = State()

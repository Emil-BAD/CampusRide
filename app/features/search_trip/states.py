from aiogram.fsm.state import StatesGroup, State


class SearchTrip(StatesGroup):
    filter_dorm = State()
    filter_building = State()
    filter_day = State()
    select_trip = State()

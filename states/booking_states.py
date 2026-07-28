from aiogram.fsm.state import State, StatesGroup

class BookingStates(StatesGroup):
    waiting_for_master = State()
    waiting_for_service = State()
    waiting_for_datetime = State()
    waiting_for_name = State()
    waiting_for_phone = State()
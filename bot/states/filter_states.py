from aiogram.fsm.state import State, StatesGroup

class CreateFilterState(StatesGroup):
    collection = State()
    model = State()
    backdrop = State()
    price = State()
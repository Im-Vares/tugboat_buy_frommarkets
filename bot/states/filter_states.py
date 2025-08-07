from aiogram.fsm.state import State, StatesGroup
class CreateFilterState(StatesGroup):
    collection = State()
    model = State()
    model_page = State()
    backdrop = State()
    backdrop_page = State()
    price = State()
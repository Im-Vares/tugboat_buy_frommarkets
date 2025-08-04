# bot/handlers.py
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from db.db import get_db
from db.filters_service import save_filter, get_filters, delete_filter
from bot.messages import GREETING_MESSAGE

router = Router()

# FSM: создание фильтра
class FilterForm(StatesGroup):
    collection = State()
    model = State()
    backdrop = State()
    price_limit = State()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(GREETING_MESSAGE)

@router.message(Command("filters"))
async def cmd_filters(message: types.Message):
    async for session in get_db():
        filters = await get_filters(session, user_id=message.from_user.id)
        if not filters:
            await message.answer("❌ У тебя пока нет фильтров.")
            return
        text = "\n\n".join([
            f"🆔 {f.id} | 🎁 <b>{f.collection}</b>\n🎭 {f.model}, 🌄 {f.backdrop}, 💰 до {f.price_limit} TON"
            for f in filters
        ])
        await message.answer(f"📦 <b>Твои фильтры:</b>\n\n{text}")

@router.message(Command("add_filter"))
async def cmd_add_filter(message: types.Message, state: FSMContext):
    await message.answer("🧩 Введи название коллекции (collection):")
    await state.set_state(FilterForm.collection)

@router.message(FilterForm.collection)
async def fsm_collection(message: types.Message, state: FSMContext):
    await state.update_data(collection=message.text.strip())
    await message.answer("🎭 Введи модель (model):")
    await state.set_state(FilterForm.model)

@router.message(FilterForm.model)
async def fsm_model(message: types.Message, state: FSMContext):
    await state.update_data(model=message.text.strip())
    await message.answer("🌅 Введи фон (backdrop):")
    await state.set_state(FilterForm.backdrop)

@router.message(FilterForm.backdrop)
async def fsm_backdrop(message: types.Message, state: FSMContext):
    await state.update_data(backdrop=message.text.strip())
    await message.answer("💸 Введи максимальную цену (TON):")
    await state.set_state(FilterForm.price_limit)

@router.message(FilterForm.price_limit)
async def fsm_price(message: types.Message, state: FSMContext):
    try:
        price = float(message.text.strip())
    except ValueError:
        await message.answer("❌ Неверный формат. Введи число.")
        return

    await state.update_data(price_limit=price)
    data = await state.get_data()

    # 💾 Сохраняем фильтр с привязкой к user_id
    async for session in get_db():
        new_filter = await save_filter(session, {
            "collection": data["collection"],
            "model": data["model"],
            "backdrop": data["backdrop"],
            "symbol": None,
            "price_limit": data["price_limit"]
        }, user_id=message.from_user.id)

    await message.answer(f"✅ Фильтр сохранён с ID: {new_filter.id}")
    await state.clear()

@router.message(Command("delete_filter"))
async def cmd_delete_filter(message: types.Message):
    await message.answer("🗑 Введи ID фильтра, который хочешь удалить:")

@router.message(F.text.regexp(r"^\d+$"))
async def handle_filter_delete(message: types.Message):
    filter_id = int(message.text.strip())
    async for session in get_db():
        success = await delete_filter(session, filter_id, user_id=message.from_user.id)
    if success:
        await message.answer(f"✅ Фильтр {filter_id} удалён.")
    else:
        await message.answer(f"❌ Не найден фильтр с ID: {filter_id}")

def register_handlers(dp):
    dp.include_router(router)
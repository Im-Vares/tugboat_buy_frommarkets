import asyncio
from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from shared.gift_cache import get_cached_collections, get_cached_backdrops, get_cached_models_for_collection
import json
from pathlib import Path

router = Router()

class FilterCreation(StatesGroup):
    choosing_collection = State()
    choosing_models = State()
    choosing_backdrops = State()
    entering_price = State()

@router.message(F.text == "/start")
async def start_cmd(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Создать фильтр", callback_data="create_filter")],
        [InlineKeyboardButton(text="👁 Посмотреть фильтры", callback_data="view_filters")],
        [InlineKeyboardButton(text="🗑 Удалить фильтр", callback_data="delete_filter")]
    ])
    await message.answer("Привет! Выбери действие:", reply_markup=kb)

@router.callback_query(F.data == "create_filter")
async def create_filter_start(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(FilterCreation.choosing_collection)
    await send_collections(callback.message)

async def send_collections(message: types.Message):
    cached = get_cached_collections()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=name, callback_data=f"coll:{name}")]
        for name in cached
    ])
    await message.answer("Выберите коллекцию:", reply_markup=kb)

@router.callback_query(F.data.startswith("coll:"))
async def choose_collection(callback: types.CallbackQuery, state: FSMContext):
    collection = callback.data.split(":")[1]
    await state.update_data(collection=collection, models=[], backdrops=[], price=None)
    models = list(get_cached_models_for_collection(collection).keys())
    await state.set_state(FilterCreation.choosing_models)
    await send_models(callback.message, state, models)

async def send_models(message: types.Message, state: FSMContext, model_list: list[str]):
    data = await state.get_data()
    selected = data.get("models", [])
    keyboard = []
    for model in model_list:
        mark = "✅" if model in selected else ""
        keyboard.append([InlineKeyboardButton(
            text=f"{mark} {model}", callback_data=f"model:{model}"
        )])
    keyboard.append([
        InlineKeyboardButton(text="⬅ Назад", callback_data="to_collections"),
        InlineKeyboardButton(text="➡ Далее", callback_data="to_backdrops")
    ])
    await message.answer("Выберите модель/модели:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@router.callback_query(F.data.startswith("model:"))
async def toggle_model(callback: types.CallbackQuery, state: FSMContext):
    model = callback.data.split(":")[1]
    data = await state.get_data()
    selected = set(data.get("models", []))
    if model in selected:
        selected.remove(model)
    else:
        selected.add(model)
    await state.update_data(models=list(selected))
    models = list(get_cached_models_for_collection(data.get("collection")).keys())
    await send_models(callback.message, state, models)

@router.callback_query(F.data == "to_collections")
async def back_to_collections(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(FilterCreation.choosing_collection)
    await send_collections(callback.message)

@router.callback_query(F.data == "to_backdrops")
async def to_backdrops(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(FilterCreation.choosing_backdrops)
    await send_backdrops(callback.message, state)

async def send_backdrops(message: types.Message, state: FSMContext):
    data = await state.get_data()
    selected = data.get("backdrops", [])
    all_backdrops = get_cached_backdrops()
    keyboard = []
    for backdrop in all_backdrops:
        mark = "✅" if backdrop in selected else ""
        keyboard.append([InlineKeyboardButton(
            text=f"{mark} {backdrop}", callback_data=f"backdrop:{backdrop}"
        )])
    keyboard.append([
        InlineKeyboardButton(text="⬅ Назад", callback_data="to_models"),
        InlineKeyboardButton(text="➡ Далее", callback_data="to_price")
    ])
    await message.answer("Выберите фон/фоны:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@router.callback_query(F.data.startswith("backdrop:"))
async def toggle_backdrop(callback: types.CallbackQuery, state: FSMContext):
    backdrop = callback.data.split(":")[1]
    data = await state.get_data()
    selected = set(data.get("backdrops", []))
    if backdrop in selected:
        selected.remove(backdrop)
    else:
        selected.add(backdrop)
    await state.update_data(backdrops=list(selected))
    await send_backdrops(callback.message, state)

@router.callback_query(F.data == "to_models")
async def to_models(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    collection = data.get("collection")
    models = list(get_cached_models_for_collection(collection).keys())
    await state.set_state(FilterCreation.choosing_models)
    await send_models(callback.message, state, models)

@router.callback_query(F.data == "to_price")
async def to_price(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(FilterCreation.entering_price)
    await callback.message.answer("Введите максимальную цену:")

@router.message(FilterCreation.entering_price)
async def set_price(message: types.Message, state: FSMContext):
    try:
        price = float(message.text)
    except ValueError:
        await message.answer("Введите корректное число!")
        return
    data = await state.get_data()
    data["price"] = price
    filters_path = Path("data/filters.json")
    filters_path.parent.mkdir(exist_ok=True)
    if filters_path.exists():
        with filters_path.open("r", encoding="utf-8") as f:
            filters = json.load(f)
    else:
        filters = []
    filters.append(data)
    with filters_path.open("w", encoding="utf-8") as f:
        json.dump(filters, f, ensure_ascii=False, indent=2)
    await message.answer("✅ Фильтр сохранён!")
    await state.clear()
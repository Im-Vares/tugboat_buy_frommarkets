import asyncio
from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from shared.gift_cache import get_cached_collections, get_cached_backdrops, get_cached_models_for_collection
import json
from pathlib import Path
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.services.search_starter import start_search_for_filter

# --- Реализация get_cached_auth (вместо импорта из bot.utils) ---
from bot.states.aportals_fetcher import get_auth_data

_cached_auth_data = None

async def get_cached_auth():
    global _cached_auth_data
    if _cached_auth_data is None:
        _cached_auth_data = await get_auth_data()
    return _cached_auth_data

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


# --- Просмотр фильтров ---
@router.callback_query(F.data == "view_filters")
async def view_filters(callback: types.CallbackQuery):
    filters_path = Path("data/filters.json")
    if not filters_path.exists():
        await callback.message.answer("❌ Нет сохранённых фильтров.")
        return

    with filters_path.open("r", encoding="utf-8") as f:
        filters = json.load(f)

    if not filters:
        await callback.message.answer("❌ Нет сохранённых фильтров.")
        return

    keyboard = InlineKeyboardBuilder()
    for idx, f in enumerate(filters, start=1):
        name = f.get("collection", "Без названия")
        keyboard.button(text=f"Фильтр {idx}: {name}", callback_data=f"filter_view:{idx}")
    await callback.message.answer("👁 Выберите фильтр для просмотра:", reply_markup=keyboard.as_markup())


@router.callback_query(F.data.startswith("filter_view:"))
async def filter_info(callback: types.CallbackQuery):
    idx = int(callback.data.split(":")[1]) - 1
    filters_path = Path("data/filters.json")
    with filters_path.open("r", encoding="utf-8") as f:
        filters = json.load(f)

    if idx >= len(filters):
        await callback.message.answer("❌ Фильтр не найден.")
        return

    f = filters[idx]
    text = (
        f"🧾 <b>Фильтр {idx + 1}</b>\n"
        f"Коллекция: <code>{f['collection']}</code>\n"
        f"Модели: <code>{', '.join(f['models'])}</code>\n"
        f"Фоны: <code>{', '.join(f['backdrops'])}</code>\n"
        f"Цена: <code>{f['price']}</code>"
    )
    await callback.message.answer(text, parse_mode="HTML")


# --- Удаление фильтров ---
@router.callback_query(F.data == "delete_filter")
async def delete_filters(callback: types.CallbackQuery):
    filters_path = Path("data/filters.json")
    if not filters_path.exists():
        await callback.message.answer("❌ Нет фильтров для удаления.")
        return

    with filters_path.open("r", encoding="utf-8") as f:
        filters = json.load(f)

    if not filters:
        await callback.message.answer("❌ Нет фильтров для удаления.")
        return

    keyboard = InlineKeyboardBuilder()
    for idx, f in enumerate(filters, start=1):
        name = f.get("collection", "Без названия")
        keyboard.button(text=f"❌ Удалить {idx}: {name}", callback_data=f"filter_delete:{idx}")
    await callback.message.answer("Выберите фильтр для удаления:", reply_markup=keyboard.as_markup())


@router.callback_query(F.data.startswith("filter_delete:"))
async def delete_filter(callback: types.CallbackQuery):
    idx = int(callback.data.split(":")[1]) - 1
    filters_path = Path("data/filters.json")
    with filters_path.open("r", encoding="utf-8") as f:
        filters = json.load(f)

    if idx >= len(filters):
        await callback.message.answer("❌ Фильтр не найден.")
        return

    del filters[idx]
    with filters_path.open("w", encoding="utf-8") as f:
        json.dump(filters, f, ensure_ascii=False, indent=2)

    await callback.message.answer("🗑 Фильтр удалён.")

async def send_collections(message: types.Message):
    cached = get_cached_collections()
    keyboard = [
        [InlineKeyboardButton(text=name, callback_data=f"coll:{name}")]
        for name in cached
    ]
    keyboard.append([
        InlineKeyboardButton(text="⬅ Назад", callback_data="start_menu"),
        InlineKeyboardButton(text="➡ Далее", callback_data="to_models")
    ])
    kb = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await message.edit_text("Выберите коллекцию:", reply_markup=kb)

@router.callback_query(F.data.startswith("coll:"))
async def choose_collection(callback: types.CallbackQuery, state: FSMContext):
    collection = callback.data.split(":")[1]
    await state.update_data(collection=collection, models=[], backdrops=[], price=None)
    await state.update_data(models_page=0)
    await state.update_data(backdrops_page=0)
    models = list(get_cached_models_for_collection(collection).keys())
    await state.set_state(FilterCreation.choosing_models)
    await send_models(callback.message, state, models)

async def send_models(message: types.Message, state: FSMContext, model_list: list[str]):
    data = await state.get_data()
    selected = data.get("models", [])
    page = data.get("models_page", 0)
    per_page = 90
    total_pages = (len(model_list) + per_page - 1) // per_page
    start = page * per_page
    end = start + per_page
    paged_models = model_list[start:end]

    keyboard = []
    # Добавляем кнопку "Выбрать все"
    keyboard.append([InlineKeyboardButton(text="✅ Выбрать все модели", callback_data="select_all_models")])

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад по списку", callback_data="models_prev"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="➡️ Далее по списку", callback_data="models_next"))
    if nav_buttons:
        keyboard.append(nav_buttons)

    for model in paged_models:
        mark = "✅" if model in selected else ""
        keyboard.append([InlineKeyboardButton(
            text=f"{mark} {model}", callback_data=f"model:{model}"
        )])
    keyboard.append([
        InlineKeyboardButton(text="⬅ Назад", callback_data="to_collections"),
        InlineKeyboardButton(text="➡ Далее", callback_data="to_backdrops")
    ])
    if len(keyboard) <= 1:
        keyboard.append([
            InlineKeyboardButton(text="⬅ Назад", callback_data="to_collections"),
            InlineKeyboardButton(text="➡ Далее", callback_data="to_backdrops")
        ])
    await message.edit_text("Выберите модель/модели:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

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
    page = data.get("backdrops_page", 0)
    per_page = 90
    total_pages = (len(all_backdrops) + per_page - 1) // per_page
    start = page * per_page
    end = start + per_page
    paged_backdrops = all_backdrops[start:end]

    keyboard = []
    # Добавляем кнопку "Выбрать все"
    keyboard.append([InlineKeyboardButton(text="✅ Выбрать все фоны", callback_data="select_all_backdrops")])

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад по списку", callback_data="backdrops_prev"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="➡️ Далее по списку", callback_data="backdrops_next"))
    if nav_buttons:
        keyboard.append(nav_buttons)

    for backdrop in paged_backdrops:
        mark = "✅" if backdrop in selected else ""
        keyboard.append([InlineKeyboardButton(
            text=f"{mark} {backdrop}", callback_data=f"backdrop:{backdrop}"
        )])
    keyboard.append([
        InlineKeyboardButton(text="⬅ Назад", callback_data="to_models"),
        InlineKeyboardButton(text="➡ Далее", callback_data="to_price")
    ])
    if len(paged_backdrops) == 0:
        keyboard.append([
            InlineKeyboardButton(text="⬅ Назад", callback_data="to_models"),
            InlineKeyboardButton(text="➡ Далее", callback_data="to_price")
        ])
    await message.edit_text("Выберите фон/фоны:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

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
    await state.update_data(models_page=0)
    await state.update_data(backdrops_page=0)
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
    auth = await get_cached_auth()
    asyncio.create_task(start_search_for_filter(data, auth))
    await message.answer("✅ Фильтр сохранён!")
    await state.clear()


# --- Выбрать все модели/фоны ---
@router.callback_query(F.data == "select_all_models")
async def select_all_models(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    collection = data.get("collection")
    all_models = list(get_cached_models_for_collection(collection).keys())
    await state.update_data(models=all_models)
    await send_models(callback.message, state, all_models)


@router.callback_query(F.data == "select_all_backdrops")
async def select_all_backdrops(callback: types.CallbackQuery, state: FSMContext):
    all_backdrops = get_cached_backdrops()
    await state.update_data(backdrops=all_backdrops)
    await send_backdrops(callback.message, state)

@router.callback_query(F.data == "start_menu")
async def return_to_start(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Создать фильтр", callback_data="create_filter")],
        [InlineKeyboardButton(text="👁 Посмотреть фильтры", callback_data="view_filters")],
        [InlineKeyboardButton(text="🗑 Удалить фильтр", callback_data="delete_filter")]
    ])
    await callback.message.edit_text("Привет! Выбери действие:", reply_markup=kb)

@router.callback_query(F.data == "models_next")
async def next_models_page(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get("models_page", 0)
    await state.update_data(models_page=page + 1)
    models = list(get_cached_models_for_collection(data.get("collection")).keys())
    await send_models(callback.message, state, models)

@router.callback_query(F.data == "models_prev")
async def prev_models_page(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get("models_page", 0)
    await state.update_data(models_page=max(page - 1, 0))
    models = list(get_cached_models_for_collection(data.get("collection")).keys())
    await send_models(callback.message, state, models)

@router.callback_query(F.data == "backdrops_next")
async def next_backdrops_page(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get("backdrops_page", 0)
    await state.update_data(backdrops_page=page + 1)
    await send_backdrops(callback.message, state)

@router.callback_query(F.data == "backdrops_prev")
async def prev_backdrops_page(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get("backdrops_page", 0)
    await state.update_data(backdrops_page=max(page - 1, 0))
    await send_backdrops(callback.message, state)
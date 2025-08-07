from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.keyboards.inline import (
    get_collections_keyboard,
    get_models_keyboard,
    get_backdrops_keyboard,
)
from bot.states.filter_states import CreateFilterState
from shared.json_filter_storage import save_filter_to_json, get_temp_filter_data, update_temp_filter_data
from bot.states.aportals_fetcher import fetch_collections, fetch_models, fetch_backdrops
import logging

logger = logging.getLogger(__name__)

router = Router()

# 👋 Начало создания фильтра
@router.callback_query(F.data == "create_filter")
async def create_filter_start(callback: types.CallbackQuery, state: FSMContext):
    await update_temp_filter_data(callback.from_user.id, {})  # сброс
    keyboard = await get_collections_keyboard()  # ⬅️ УБРАЛ collections внутри
    if not keyboard.inline_keyboard:
        await callback.message.answer("❌ Не удалось получить коллекции")
        return
    await callback.message.answer("Выберите коллекцию:", reply_markup=keyboard)
    await state.set_state(CreateFilterState.collection)

# 📦 Коллекция
@router.callback_query(CreateFilterState.collection)
async def collection_chosen(callback: types.CallbackQuery, state: FSMContext):
    collection = callback.data.split("collection:")[-1]
    await update_temp_filter_data(callback.from_user.id, {"collection": collection, "models": [], "backdrops": []})
    models = await fetch_models(collection)
    await callback.message.edit_text(
        f"Коллекция: {collection}\nВыберите модель или модели:",
        reply_markup=await get_models_keyboard(models, [])
    )
    await state.set_state(CreateFilterState.model)

# 🧙️ Модели (multi select)
@router.callback_query(CreateFilterState.model)
async def model_chosen(callback: types.CallbackQuery, state: FSMContext):
    model = callback.data
    user_id = callback.from_user.id
    data = await get_temp_filter_data(user_id)
    selected = data.get("models", [])

    if model == "next":
        backdrops = await fetch_backdrops(data["collection"])
        await callback.message.edit_text(
            "Выберите фон или фоны:",
            reply_markup=await get_backdrops_keyboard(backdrops, [])
        )
        await state.set_state(CreateFilterState.backdrop)
        return
    elif model == "back":
        collections = await fetch_collections()
        await callback.message.edit_text(
            "Выберите коллекцию:",
            reply_markup=await get_collections_keyboard(collections)
        )
        await state.set_state(CreateFilterState.collection)
        return

    if model in selected:
        selected.remove(model)
    else:
        selected.append(model)

    await update_temp_filter_data(user_id, {"models": selected})
    models = await fetch_models(data["collection"])
    await callback.message.edit_reply_markup(
        reply_markup=await get_models_keyboard(models, selected)
    )

# 🌄 Фоны
@router.callback_query(CreateFilterState.backdrop)
async def backdrop_chosen(callback: types.CallbackQuery, state: FSMContext):
    backdrop = callback.data
    user_id = callback.from_user.id
    data = await get_temp_filter_data(user_id)
    selected = data.get("backdrops", [])

    if backdrop == "next":
        await callback.message.edit_text("💰 Введите макс. цену:")
        await state.set_state(CreateFilterState.price)
        return
    elif backdrop == "back":
        models = await fetch_models(data["collection"])
        await callback.message.edit_text(
            "Выберите модель или модели:",
            reply_markup=await get_models_keyboard(models, data["models"])
        )
        await state.set_state(CreateFilterState.model)
        return

    if backdrop in selected:
        selected.remove(backdrop)
    else:
        selected.append(backdrop)

    await update_temp_filter_data(user_id, {"backdrops": selected})
    backdrops = await fetch_backdrops(data["collection"])
    await callback.message.edit_reply_markup(
        reply_markup=await get_backdrops_keyboard(backdrops, selected)
    )

# 💰 Цена
@router.message(CreateFilterState.price)
async def price_entered(message: types.Message, state: FSMContext):
    try:
        price = float(message.text.replace(",", "."))
        user_id = message.from_user.id
        data = await get_temp_filter_data(user_id)
        data["price_limit"] = price
        await save_filter_to_json(user_id, data)

        await message.answer("✅ Фильтр успешно создан!")
        await state.clear()
    except ValueError:
        await message.answer("Введите корректное число (2.5)")

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from shared.gift_cache import (
    get_cached_collections,
    get_cached_models_for_collection,
    get_cached_backdrops,
)

# 👑 Коллекции
async def get_collections_keyboard() -> InlineKeyboardMarkup:
    collections = get_cached_collections()
    buttons = [
        [InlineKeyboardButton(text=col, callback_data=f"collection:{col}")]
        for col in collections
    ]
    buttons.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="collection:back"),
        InlineKeyboardButton(text="➡️ Далее", callback_data="collection:next")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# 🧩 Модели
async def get_models_keyboard(collection: str, selected_models: list[str]) -> InlineKeyboardMarkup:
    models = get_cached_models_for_collection(collection)
    buttons = []

    buttons.append([
        InlineKeyboardButton(text="✅ Выбрать все модели", callback_data="model:select_all")
    ])

    for model in models:
        mark = "✅ " if model in selected_models else ""
        buttons.append([
            InlineKeyboardButton(
                text=f"{mark}{model}",
                callback_data=f"model:{model}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="model:back"),
        InlineKeyboardButton(text="➡️ Далее", callback_data="model:next")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

# 🌄 Фоны
async def get_backdrops_keyboard(selected_backdrops: list[str]) -> InlineKeyboardMarkup:
    backdrops = get_cached_backdrops()
    buttons = []

    buttons.append([
        InlineKeyboardButton(text="✅ Выбрать все фоны", callback_data="backdrop:select_all")
    ])

    for bd in backdrops:
        mark = "✅ " if bd in selected_backdrops else ""
        buttons.append([
            InlineKeyboardButton(
                text=f"{mark}{bd}",
                callback_data=f"backdrop:{bd}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="backdrop:back"),
        InlineKeyboardButton(text="➡️ Далее", callback_data="backdrop:next")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
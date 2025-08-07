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
async def get_models_keyboard(collection: str, selected_models: list[str], page: int = 0) -> InlineKeyboardMarkup:
    models = get_cached_models_for_collection(collection)
    buttons = []

    page_size = 90
    paged_models = models[page * page_size : (page + 1) * page_size]

    buttons.append([
        InlineKeyboardButton(text="✅ Выбрать все модели", callback_data="model:select_all")
    ])

    if len(models) > page_size:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад по списку", callback_data=f"model:page:{page - 1}"))
        if (page + 1) * page_size < len(models):
            nav_buttons.append(InlineKeyboardButton(text="➡️ Далее по списку", callback_data=f"model:page:{page + 1}"))
        buttons.append(nav_buttons)

    for model in paged_models:
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
async def get_backdrops_keyboard(selected_backdrops: list[str], page: int = 0) -> InlineKeyboardMarkup:
    backdrops = get_cached_backdrops()
    buttons = []

    page_size = 90
    paged_backdrops = backdrops[page * page_size : (page + 1) * page_size]

    buttons.append([
        InlineKeyboardButton(text="✅ Выбрать все фоны", callback_data="backdrop:select_all")
    ])

    if len(backdrops) > page_size:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад по списку", callback_data=f"backdrop:page:{page - 1}"))
        if (page + 1) * page_size < len(backdrops):
            nav_buttons.append(InlineKeyboardButton(text="➡️ Далее по списку", callback_data=f"backdrop:page:{page + 1}"))
        buttons.append(nav_buttons)

    for bd in paged_backdrops:
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
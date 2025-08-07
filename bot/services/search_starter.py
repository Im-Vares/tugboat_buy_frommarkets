from aportalsmp import search
from aiogram import Bot
from aiogram.types import Message
import os
import json

PENDING_GIFTS_PATH = "data/pending_gifts.json"

def load_pending_gifts() -> list:
    if os.path.exists(PENDING_GIFTS_PATH):
        with open(PENDING_GIFTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_pending_gifts(gifts: list):
    with open(PENDING_GIFTS_PATH, "w", encoding="utf-8") as f:
        json.dump(gifts, f, indent=2, ensure_ascii=False)

def append_pending_gift(gift: dict, tg_id: str):
    current = load_pending_gifts()
    gift["tg_id"] = tg_id
    gift["status"] = "✅ Подходит по фильтру"
    current.append(gift)
    save_pending_gifts(current)

bot_instance: Bot = None  # You can assign the actual bot instance if needed

async def notify_found_gift(gift_data: dict):
    print(f"Подарок найден: {gift_data.model_dump() if hasattr(gift_data, 'model_dump') else gift_data.__dict__}")
    append_pending_gift(gift_data.model_dump() if hasattr(gift_data, "model_dump") else gift_data.__dict__, getattr(gift_data, "chat_id", ""))
    if bot_instance:
        await bot_instance.send_message(chat_id=gift_data.get("chat_id", ""), text="🎁 Найден подарок по фильтру!")
import asyncio

async def start_search_for_filter(filter_data: dict, auth):
    collection = filter_data.get("collection")
    models = filter_data.get("models", [])
    backdrops = filter_data.get("backdrops", [])
    max_price = filter_data.get("price")

    async def run_search():
        while True:
            try:
                results = await search(
                    gift_name=collection,
                    model=models,
                    backdrop=backdrops,
                    authData=auth
                )
                if results:
                    await notify_found_gift(results[0])
                    break
            except Exception as e:
                print(f"Ошибка при поиске подарков: {e}")
            await asyncio.sleep(5)

    asyncio.create_task(run_search())


# --- Added function for starting search for all saved filters ---
import json
FILTER_FILE_PATH = "data/filters.json"
from bot.states.aportals_fetcher import get_auth_data

async def start_search_for_all_filters():
    try:
        with open(FILTER_FILE_PATH, "r", encoding="utf-8") as f:
            filters = json.load(f)

        auth = await get_auth_data()

        for filter_data in filters:
            await start_search_for_filter(filter_data, auth)

    except Exception as e:
        print(f"Ошибка при старте автопоиска по сохранённым фильтрам: {e}")
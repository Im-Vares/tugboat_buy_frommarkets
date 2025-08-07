import asyncio
import json
from pathlib import Path
from loguru import logger
from aportalsmp import collections, filterFloors
from aportalsmp.auth import update_auth
from config import API_ID, API_HASH, SESSION_NAME

# Путь к JSON-хранилищу
CACHE_PATH = Path("data/gift_cache.json")
CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)

# === Авторизация с retry ===
async def get_auth_data(retries: int = 3, delay: int = 5):
    for attempt in range(retries):
        try:
            logger.info(f"🔒 Авторизация {attempt + 1}/{retries}")
            return await update_auth(api_id=API_ID, api_hash=API_HASH, session_name=SESSION_NAME)
        except Exception as e:
            logger.warning(f"❌ Ошибка авторизации (попытка {attempt + 1}): {e}")
            if attempt < retries - 1:
                await asyncio.sleep(delay * (attempt + 1))
    logger.critical("🛑 Не удалось авторизоваться после всех попыток")
    return None

# === Загрузка кэша ===
def load_cache() -> dict:
    if CACHE_PATH.exists():
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# === Сохранение кэша ===
def save_cache(data: dict):
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# === Получение ВСЕХ коллекций ===
async def fetch_collections() -> list[str]:
    cache = load_cache()
    if "collections" in cache:
        logger.info("📦 Коллекции взяты из кэша")
        return list(cache["collections"].keys())

    auth_data = await get_auth_data()
    if not auth_data:
        return []

    try:
        data = await collections(authData=auth_data)
        collections_dict = {
            c.get("short_name"): {} for c in getattr(data, "_collections", []) if c.get("short_name")
        }
        logger.success(f"✅ Найдено коллекций: {len(collections_dict)}")

        cache["collections"] = collections_dict
        save_cache(cache)
        return list(collections_dict.keys())
    except Exception as e:
        logger.error(f"❌ Ошибка получения коллекций: {e}")
        return []

# === Получение ВСЕХ моделей по коллекции ===
async def fetch_models(collection: str) -> list[str]:
    cache = load_cache()
    if collection in cache.get("collections", {}) and "models" in cache["collections"][collection]:
        logger.info(f"🧩 Модели для {collection} взяты из кэша")
        return cache["collections"][collection]["models"]

    auth_data = await get_auth_data()
    if not auth_data:
        return []

    try:
        filters = await filterFloors(gift_name=collection, authData=auth_data)
        models = filters.models if filters and filters.models else []
        logger.debug(f"🧩 Модели для {collection}: {models}")

        cache.setdefault("collections", {}).setdefault(collection, {})["models"] = models
        save_cache(cache)
        return models
    except Exception as e:
        logger.error(f"❌ Ошибка получения моделей для {collection}: {e}")
        return []

# === Получение ВСЕХ фонов (глобально, не по коллекции) ===
async def fetch_backdrops(_: str = None) -> list[str]:
    cache = load_cache()
    if "backdrops" in cache:
        logger.info("🌄 Фоны взяты из кэша")
        return cache["backdrops"]

    auth_data = await get_auth_data()
    if not auth_data:
        return []

    try:
        # Используем любую коллекцию для получения фонов (например первую)
        collections_list = await fetch_collections()
        if not collections_list:
            return []
        filters = await filterFloors(gift_name=collections_list[0], authData=auth_data)
        backdrops = filters.backdrops if filters and filters.backdrops else []
        logger.debug(f"🌄 Фоны: {backdrops}")

        cache["backdrops"] = backdrops
        save_cache(cache)
        return backdrops
    except Exception as e:
        logger.error(f"❌ Ошибка получения фонов: {e}")
        return []
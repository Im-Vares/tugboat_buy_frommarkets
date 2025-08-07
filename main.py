import asyncio
import sys
import os
from dotenv import load_dotenv
from loguru import logger

# Пробрасываем путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from session import get_pyrogram_client
from bot.bot import start_bot  # bot/бот запускается отсюда
from bot.states.aportals_fetcher import get_auth_data
from aportalsmp import filterFloors, collections
from shared.gift_cache import (
    cache_backdrops,
    get_cached_collections,
    cache_models_for_collection,
)

load_dotenv()


async def preload_backdrops_once():
    logger.info("📦 Проверка кэша фонов...")
    try:
        auth = await get_auth_data()
        filters = await filterFloors(gift_name="plushpepe", authData=auth)
        if filters and filters.backdrops:
            cache_backdrops(filters.backdrops)
            logger.success("✅ Фоны успешно закэшированы")
        else:
            logger.warning("⚠️ Не удалось получить фоны")
    except Exception as e:
        logger.error(f"❌ Ошибка при кэшировании фонов: {e}")


async def preload_some_collections(limit: int = 4):
    logger.info("📦 Подгрузка коллекций в кэш...")
    try:
        auth = await get_auth_data()
        all_collections = await collections(authData=auth)
        cached = get_cached_collections()

        to_load = [
            c["short_name"] for c in all_collections._collections
            if c.get("short_name") and c["short_name"] not in cached
        ][:limit]

        for short_name in to_load:
            logger.info(f"➡️ Кэшируем модели коллекции: {short_name}")
            filters = await filterFloors(gift_name=short_name, authData=auth)
            if filters:
                cache_models_for_collection(auth, short_name, filters.models)
            else:
                logger.warning(f"⚠️ Не удалось получить модели для: {short_name}")

        logger.success("✅ Первичная подгрузка коллекций завершена")
    except Exception as e:
        logger.error(f"❌ Ошибка при кэшировании коллекций: {e}")


async def runner():
    await preload_backdrops_once()
    await preload_some_collections(limit=4)

    pyrogram_client = get_pyrogram_client()
    await pyrogram_client.start()
    try:
        await asyncio.gather(
            start_bot()
        )
    finally:
        await pyrogram_client.stop()


if __name__ == "__main__":
    asyncio.run(runner())
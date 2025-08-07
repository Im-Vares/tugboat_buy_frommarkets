# worker/autobuy_worker.py

import asyncio
from aportals.search_logic import init_aportals, search_gifts_by_filter
from shared.json_filter_storage import load_all_filters
from loguru import logger

async def autobuy_loop():
    logger.info("🚀 Запуск автообновления фильтров...")

    await init_aportals()  # обязательно инициализируем клиента

    while True:
        filters = load_all_filters()  # загружаем все фильтры из JSON

        for f in filters:
            try:
                await search_gifts_by_filter(
                    collection=f['collection'],
                    model=f['model'],
                    backdrop=f['backdrop'],
                    price_limit=f['price_limit'],
                    filter_id=f['id'],
                    user_id=f['user_id']
                )
            except Exception as e:
                logger.error(f"❌ Ошибка при обработке фильтра {f['id']}: {e}")

        await asyncio.sleep(0.1)
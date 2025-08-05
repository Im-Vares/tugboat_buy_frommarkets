# worker/autobuy_worker.py

import asyncio
from db.db import get_db
from db.filters_service import get_filters
from aportals.search_logic import init_aportals, search_gifts_by_filter
from loguru import logger


async def autobuy_loop():
    logger.info("🚀 Запуск автообновления фильтров...")

    await init_aportals()  # обязательно инициализируем клиента

    while True:
        async for session in get_db():
            filters = await get_filters(session)  # все фильтры всех юзеров
            for f in filters:
                try:
                    await search_gifts_by_filter(
                        collection=f.collection,
                        model=f.model,
                        backdrop=f.backdrop,
                        price_limit=f.price_limit,
                        filter_id=f.id,
                        user_id=f.user_id  # 👈 добавили передачу user_id
                    )
                except Exception as e:
                    logger.error(f"❌ Ошибка при обработке фильтра {f.id}: {e}")

        await asyncio.sleep(0.1)
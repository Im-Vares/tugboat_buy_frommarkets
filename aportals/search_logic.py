# aportals/search_logic.py

import asyncio
from loguru import logger
from aportalsmp.auth import update_auth
from aportalsmp.gifts import search
from config import API_ID, API_HASH

async def search_gifts_by_filter(collection: str, model: str, backdrop: str, price_limit: float):
    try:
        auth = await update_auth(API_ID, API_HASH)
        logger.info(f"📡 Поиск подарков: {collection} | {model} | {backdrop} | до {price_limit} TON")

        results = await search(
            sort="price_asc",
            offset=0,
            limit=10,
            gift_name=collection,
            model=model,
            backdrop=backdrop,
            symbol=[],
            min_price=1,
            max_price=999999,
            authData=auth
        )

        if not results:
            logger.warning("❌ Подарки не найдены.")
            return []

        matched = []
        for gift in results:
            match = {
                "id": gift.id,
                "name": gift.name,
                "price": gift.price,
                "status": "✅ можно брать" if gift.price <= price_limit else "⚠️ цена выше лимита"
            }
            matched.append(match)

        return matched

    except Exception as e:
        logger.error(f"Ошибка при поиске: {e}")
        return []
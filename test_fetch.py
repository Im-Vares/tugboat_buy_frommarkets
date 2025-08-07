import asyncio
from loguru import logger
from bot.states.aportals_fetcher import fetch_collections, fetch_models, fetch_backdrops

async def main():
    logger.info("🧠 Получаю коллекции...")
    collections = await fetch_collections()
    print(f"Найдено коллекций: {len(collections)}")

    for coll in collections:
        print(f"🧠 Обрабатываем коллекцию: {coll}")
        
        models = await fetch_models(coll)
        print(f"Моделей: {len(models)}")
        for m in models:
            print(f"🧱 {m}")
        
        print("-" * 30)

if __name__ == "__main__":
    asyncio.run(main())
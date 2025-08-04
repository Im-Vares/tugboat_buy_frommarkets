# main.py

import asyncio
from aportals.aportals_handler import init_aportals
from aportals.search_logic import search_gifts_by_filter
from db.db import get_db, engine
from db.models import Base
from db.filters_service import save_filter


async def main():
    # 🔧 Миграция таблиц
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # ✅ Авторизация
    auth = await init_aportals()
    if not auth:
        print("❌ Не удалось авторизоваться.")
        return

    # 🧾 Ввод данных
    print("\n🔍 Введите данные для фильтра:")
    collection = input("Название подарка (collection): ").strip()
    model = input("Модель (model): ").strip()
    backdrop = input("Фон (backdrop): ").strip()
    price_limit = float(input("Максимальная цена (TON): ").strip())

    filter_data = {
        "collection": collection,
        "model": model,
        "backdrop": backdrop,
        "symbol": None,
        "price_limit": price_limit
    }

    # 💾 Сохраняем фильтр в БД
    async for session in get_db():
        saved = await save_filter(session, filter_data)
        print(f"\n✅ Фильтр сохранён с ID: {saved.id}")

    # 🔍 Поиск по фильтру
    gifts = await search_gifts_by_filter(
        collection=collection,
        model=model,
        backdrop=backdrop,
        price_limit=price_limit
    )

    # 📦 Результаты
    if not gifts:
        print("❌ Подарки не найдены.")
        return

    for g in gifts:
        print(f"\n🎁 {g['name']}")
        print(f"💰 Цена: {g['price']} TON")
        print(f"📌 ID: {g['id']}")
        print(f"{g['status']}")

if __name__ == "__main__":
    asyncio.run(main())
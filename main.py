# main.py

import asyncio
from aportals.aportals_handler import init_aportals
from aportals.search_logic import search_gifts_by_filter

async def main():
    # Авторизация и баланс
    auth = await init_aportals()
    if not auth:
        print("❌ Не удалось авторизоваться.")
        return

    # Ввод параметров
    print("\n🔍 Введите данные для поиска подарков:")
    collection = input("Название подарка (collection): ").strip()
    model = input("Модель (model): ").strip()
    backdrop = input("Фон (backdrop): ").strip()
    price_limit = float(input("Максимальная цена (TON): ").strip())

    # Поиск
    gifts = await search_gifts_by_filter(
        collection=collection,
        model=model,
        backdrop=backdrop,
        price_limit=price_limit
    )

    # Результаты
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
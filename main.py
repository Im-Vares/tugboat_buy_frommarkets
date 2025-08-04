# main.py

import asyncio
from db.db import engine
from db.models import Base
from bot.bot import start_bot            # Telegram-бот
from worker.autobuy_worker import autobuy_loop  # Автоскан по фильтрам

async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def main():
    await setup_database()

    # 🔥 Запускаем бот + автоскан одновременно
    await asyncio.gather(
        start_bot(),
        autobuy_loop()
    )

if __name__ == "__main__":
    asyncio.run(main())
# main.py

import asyncio
from db.db import engine
from db.models import Base
from bot.bot import start_bot  # Telegram-бот

async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def main():
    # 🔧 Миграция
    await setup_database()

    # 🚀 Запуск Telegram-бота
    await start_bot()

if __name__ == "__main__":
    asyncio.run(main())
import asyncio
import logging
from aiogram import Bot, Dispatcher
from config.config import settings
from bot.commands import register_commands
from bot.filters_fsm import router as filters_router

async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.info("Bot starting…")

    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(filters_router)

    # Лог старта в БД — внутри функции, без "await outside function"
    try:
        from db.db_class import DB
        await DB().log("bot", "start", "ok", details="bot started")
    except Exception as e:
        logging.warning(f"DB log failed: {e}")

    register_commands(dp)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
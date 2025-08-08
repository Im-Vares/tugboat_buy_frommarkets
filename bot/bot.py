import asyncio
from aiogram import Bot, Dispatcher
from config.config import settings
from bot.commands import register_commands

async def main():
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher()
    register_commands(dp)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

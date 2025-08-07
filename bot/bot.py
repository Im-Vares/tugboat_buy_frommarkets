# bot/bot.py

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from bot.handlers import router

# 🧠 Правильный способ указать parse_mode в новых версиях aiogram
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()

async def start_bot():
    dp.include_router(router)
    await dp.start_polling(bot)
from aiogram import Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from config.config import settings
from aportals_api.client import my_balances
from db.db_class import DB

db = DB()

def _is_allowed(user_id: int) -> bool:
    return (not settings.ALLOWED_USERS) or (user_id in settings.ALLOWED_USERS)

async def cmd_start(message: Message):
    if not _is_allowed(message.from_user.id):
        return await message.answer("Доступ запрещён.")
    await message.answer("Доступ разрешён. Команды: /balance, /filters")

async def cmd_balance(message: Message):
    if not _is_allowed(message.from_user.id):
        return await message.answer("Доступ запрещён.")
    b = await my_balances()
    await message.answer(f"Баланс: {b.balance} TON, заморожено: {b.frozen_funds} TON")

async def cmd_filters(message: Message):
    if not _is_allowed(message.from_user.id):
        return await message.answer("Доступ запрещён.")
    rows = await db.filters_active()
    if not rows:
        return await message.answer("Фильтров пока нет.")
    text = "\n".join([
        f"#{r['id']} | {r['collection']} | model={r['model']} | backdrop={r['backdrop']} | <= {r['max_price']} TON | qty={r['quantity']} | {'ON' if r['active'] else 'OFF'}"
        for r in rows
    ])
    await message.answer(text)

def register_commands(dp: Dispatcher):
    dp.message.register(cmd_start, Command(commands=["start"]))
    dp.message.register(cmd_balance, Command(commands=["balance"]))
    dp.message.register(cmd_filters, Command(commands=["filters"]))

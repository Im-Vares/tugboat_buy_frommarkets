# aportals/aportals_handler.py

import asyncio
from loguru import logger
from config import API_ID, API_HASH
from aportalsmp.auth import update_auth
from aportalsmp.account import myBalances

auth_data: str | None = None  # Глобальный токен

async def init_aportals():
    global auth_data

    logger.info("🔌 Инициализация подключения к aportalsmp...")

    try:
        # Получаем authData строку
        auth_data = await update_auth(
            api_id=API_ID,
            api_hash=API_HASH,
        )
        logger.success("✅ Успешная авторизация через aportalsmp.")

        # Получаем баланс аккаунта
        balances = await myBalances(auth_data)
        logger.info(f"💰 Баланс: {balances.balance}")
        logger.info(f"❄️ Заморожено: {balances.frozen_funds}")

        return auth_data

    except Exception as e:
        logger.error(f"❌ Ошибка при инициализации aportalsmp: {e}")
        return None
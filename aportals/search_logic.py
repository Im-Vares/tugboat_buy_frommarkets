from pathlib import Path
import json
import re
from aportalsmp.gifts import search
from aportalsmp.auth import update_auth
from db.pending_gift_service import save_pending_gift, is_gift_already_pending
from db.db import get_db
from loguru import logger
from config import API_ID, API_HASH, SESSION_NAME, BOT_TOKEN
from shared.utils import get_filter_filename  # ✅ общий метод имени файла
from aiogram import Bot

authData = None
bot = Bot(token=BOT_TOKEN)


async def init_aportals():
    global authData
    logger.info("🔌 Авторизация в APortals...")
    try:
        authData = await update_auth(
            api_id=API_ID,
            api_hash=API_HASH,
            session_name=SESSION_NAME
        )
        logger.success("✅ Авторизация прошла успешно!")
    except Exception as e:
        logger.error(f"❌ Ошибка авторизации: {e}")
        authData = None


async def search_gifts_by_filter(collection: str, model: str, backdrop: str, price_limit: float, filter_id: int, user_id: int):
    if not authData:
        raise ValueError("❌ authData не инициализирован, вызови init_aportals()")

    logger.info(f"🔎 Ищем подарки: collection='{collection}' model='{model}' backdrop='{backdrop}' price_limit={price_limit}")

    try:
        gifts = await search(
            sort="price_asc",
            gift_name=collection or "",
            model=model or "",
            backdrop=backdrop or "",
            max_price=price_limit,
            authData=authData
        )
    except Exception as e:
        logger.error(f"❌ Ошибка при поиске через API: {e}")
        return []

    result = []

    async for session in get_db():
        for g in gifts:
            price = g.price
            if price is None:
                continue

            gift_id = g.id or getattr(g, "nft_id", None)
            if not gift_id:
                continue

            g_dict = g.__dict__.copy()

            if price <= price_limit:
                already_saved = await is_gift_already_pending(session, filter_id, gift_id)
                if not already_saved:
                    logger.success(f"🎁 Новый подходящий подарок: {g.name} за {price} TON")
                    await save_pending_gift(session, filter_id, g_dict)

                    # 📤 Уведомление в Telegram
                    photo = g_dict.get("photo_url")
                    price_val = g_dict.get("price")
                    name = g_dict.get("name", "Подарок")
                    if photo and price_val:
                        try:
                            await bot.send_photo(
                                chat_id=user_id,
                                photo=photo,
                                caption=(
                                    f"🎁 <b>{name}</b>\n"
                                    f"💰 Цена: <b>{price_val} TON</b>\n\n"
                                    f"✅ Подходит по фильтру. Ожидаем покупку..."
                                ),
                                parse_mode="HTML"
                            )
                        except Exception as e:
                            logger.error(f"❌ Ошибка при отправке уведомления: {e}")
                else:
                    logger.debug(f"🔁 Подарок уже был найден: {gift_id}")

                g_dict["status"] = "✅ Подходит по фильтру"
            else:
                g_dict["status"] = f"❌ Дорогой: {price} TON > {price_limit} TON"

            result.append(g_dict)

    # 💾 Сохраняем в уникальный файл
    try:
        Path("data").mkdir(parents=True, exist_ok=True)
        filename = get_filter_filename(collection, model, backdrop, price_limit)
        output_path = Path("data") / filename

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        logger.info(f"📦 Сохранили подарки фильтра в {output_path}")
    except Exception as e:
        logger.error(f"❌ Ошибка при сохранении JSON-файла: {e}")

    return result
from pathlib import Path
import json
from aportalsmp.gifts import search
from aportalsmp.auth import update_auth
from loguru import logger
from config import API_ID, API_HASH, SESSION_NAME, BOT_TOKEN
from shared.utils import get_filter_filename, send_json_to_socket
from aiogram import Bot

# Путь к JSON с найденными подарками и фильтрами
FILTERS_JSON_PATH = Path("filters.json")
PENDING_GIFTS_DIR = Path("data")

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

def _load_pending_json(filepath: Path) -> list:
    if filepath.exists():
        with open(filepath, encoding="utf-8") as f:
            return json.load(f)
    return []

def _save_pending_json(filepath: Path, data: list):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

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
    filter_filename = get_filter_filename(collection, model, backdrop, price_limit)
    pending_path = PENDING_GIFTS_DIR / filter_filename
    Path("data").mkdir(parents=True, exist_ok=True)

    pending_list = _load_pending_json(pending_path)
    pending_ids = {g.get("id") or g.get("nft_id") for g in pending_list}

    for g in gifts:
        price = g.price
        gift_id = g.id or getattr(g, "nft_id", None)
        if not gift_id or price is None:
            continue

        g_dict = g.__dict__.copy()
        g_dict["user_id"] = user_id
        g_dict["filter_id"] = filter_id

        if price <= price_limit:
            if gift_id not in pending_ids:
                logger.success(f"🎁 Новый подходящий подарок: {g.name} за {price} TON")
                g_dict["status"] = "✅ Подходит по фильтру"
                pending_list.append(g_dict)

                # 📤 Уведомление в Telegram
                try:
                    await bot.send_photo(
                        chat_id=user_id,
                        photo=g_dict.get("photo_url"),
                        caption=(
                            f"🎁 <b>{g_dict.get('name', 'Подарок')}</b>\n"
                            f"💰 Цена: <b>{price} TON</b>\n\n"
                            f"✅ Подходит по фильтру. Ожидаем покупку..."
                        ),
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.error(f"❌ Ошибка при отправке уведомления: {e}")

                send_json_to_socket(g_dict)
            else:
                logger.debug(f"🔁 Подарок уже был найден: {gift_id}")
        else:
            g_dict["status"] = f"❌ Дорогой: {price} TON > {price_limit} TON"

        result.append(g_dict)

    _save_pending_json(pending_path, pending_list)
    logger.info(f"📦 Сохранили подарки фильтра в {pending_path}")

    return result
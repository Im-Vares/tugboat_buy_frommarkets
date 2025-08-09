# APortals Gift Autopurchase System

## Компоненты
1. **Telegram-бот** — управление фильтрами и пользователями, просмотр баланса.
2. **Search Worker** — ищет подарки по активным фильтрам и передает в покупку.
3. **Buy Worker** — принимает кандидатов и покупает их.

## Формат JSON (NDJSON, одна строка = один подарок)
```json
{"nft_id": "1234567890", "tg_id": "98765", "collection": "Plush Pepe", "price": 3.2, "filter_id": 12}
```

## Частота
- Каждые `SEARCH_INTERVAL` секунд (в .env), напр. `0.2` — Search Worker делает тик поиска и отправляет найденные JSON в Buy Worker.

## Запуск
1. Скопируйте `.env.example` → `.env` и заполните токены/DSN/интервалы.
2. `pip install -r requirements.txt`
3. Инициализируйте БД: `python -m db.init_db`
4. Запустите процессы:
    - `python -m workers.buy_worker`
    - `python -m workers.search_worker`
    - (опционально) `python -m bot.bot`
\n\n## Runtime (Portals, no markets layer)
- `workers/search_worker.py` опрашивает Portals каждые `SEARCH_INTERVAL` сек (0.2 по умолчанию) через `aportals_api.client.search`.
- Находит подходящие лоты → шлёт JSON в `buy_worker` по TCP.
- `workers/buy_worker.py` проверяет баланс (`aportals_api.client.my_balances`) и покупает (`aportals_api.client.buy`).
- FSM бота: коллекция → модели → фоны → max_price → qty → подтверждение. Подсказки: `/collections [q]`.\n


BOT_TOKEN=
ALLOWED_USERS=
TG_API_ID=
TG_API_HASH=
SESSION_PATH=./data
SESSION_NAME=account
DB_DSN=postgresql://user:pass@localhost:5432/aportals
SEARCH_INTERVAL=0.2
SEARCH_LIMIT=50
BUY_HOST=127.0.0.1
BUY_PORT=8765

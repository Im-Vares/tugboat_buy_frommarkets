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

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


## Обновление до мультивыборных фильтров (модели/фоны — массивы)

### Миграция БД
Разово выполнить:
```sql
\i db/migrations/2025-08-08_model_backdrop_arrays.sql
```

### Поиск/Покупка
`workers/search_worker.py` теперь поддерживает множественный выбор `model/backdrop` (TEXT[]). Пустые списки означают "любой".

### Логи старта
Бот и воркеры пишут логи при старте (stdout) и строку в таблицу `logs`.

### Деплой одной командой
Создайте локально `deploy.sh` и выполните:
```bash
bash deploy.sh
```
Пример `deploy.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail
ssh ubuntu@VM1 'cd ~/aportals_project && git pull --rebase && . .venv/bin/activate && pip install -r requirements.txt && sudo systemctl restart aportals-buy'
ssh ubuntu@VM2 'cd ~/aportals_project && git pull --rebase && . .venv/bin/activate && pip install -r requirements.txt && sudo systemctl restart aportals-search && sudo systemctl restart aportals-bot'
```

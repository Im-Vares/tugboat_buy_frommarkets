# 🛍️ Tugboat Buy from Markets

Асинхронный Telegram-проект для **автоматического поиска и покупки NFT-подарков** с платформы Fragment через библиотеку `aportalsmp`.

---

## 🚀 Описание проекта

Система позволяет:
- Авторизоваться на портале APortals.
- Хранить фильтры поиска подарков в PostgreSQL.
- Асинхронно искать подарки по фильтрам и сохранять JSON с найденными.
- Исключать повторные совпадения (anti-спам).
- Передавать JSON на второй воркер (покупщик) по сокетам.
- Вести логгирование всех операций.
- Удалять фильтры и связанные с ними `.json`-файлы из `data/`.

---

## 📂 Структура проекта

```bash
.
├── bot/                  # Telegram-бот (aiogram)
│   ├── handlers/         # Обработчики команд
│   ├── services/         # Логика (работа с пользователями, фильтрами и т.д.)
│   └── bot.py            # Запуск бота

├── db/                   # База данных (PostgreSQL + SQLAlchemy)
│   ├── models.py         # ORM-модели (User, Filter, PendingGift)
│   ├── db.py             # Подключение к БД и сессия
│   ├── filters_service.py        # CRUD для фильтров с удалением JSON
│   └── pending_gift_service.py # Работа с найденными подарками

├── worker/               # Воркеры
│   ├── search_worker.py  # Поиск подарков по фильтрам (каждые X секунд)
│   ├── autobuy_worker.py # Получение JSON и покупка через `.buy()`
│   └── socket_client.py  # TCP-сокет клиент

├── aportals/             # Работа с API APortals
│   ├── auth.py           # Авторизация
│   └── search_logic.py   # Поиск и сохранение подарков по фильтрам

├── config.py             # Конфиг с переменными из .env
├── .env.example          # Пример .env файла
├── requirements.txt      # Зависимости
└── main.py               # Точка запуска бота и воркеров


⚙️ Как запустить
pip install -r requirements.txt


Создай .env на основе .env.example:
API_ID=...
API_HASH=...
SESSION_NAME=...
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/dbname


Запусти проект:
python main.py


💾 Формат JSON-файлов
Все найденные подарки сохраняются в data/ с именем:
{collection}_{model}_{backdrop}_{price_limit}.json


Пример:
Snoop_Dogg_Team_USA_Coral_Red_4.0.json
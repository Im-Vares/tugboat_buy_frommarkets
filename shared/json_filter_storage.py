import json
from pathlib import Path

# 📂 Папка хранения
DATA_DIR = Path("data")
FILTERS_FILE = DATA_DIR / "filters.json"
TEMP_DIR = DATA_DIR / "temp_filters"

DATA_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# ==========================
# 🔁 ВРЕМЕННЫЕ ДАННЫЕ (по user_id)
# ==========================

def get_temp_path(user_id: int) -> Path:
    return TEMP_DIR / f"{user_id}.json"


async def get_temp_filter_data(user_id: int) -> dict:
    path = get_temp_path(user_id)
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


async def update_temp_filter_data(user_id: int, update: dict):
    data = await get_temp_filter_data(user_id)
    data.update(update)
    with open(get_temp_path(user_id), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


async def save_filter_to_json(user_id: int, filter_data: dict):
    filters = load_all_filters()
    filters.append({
        "user_id": user_id,
        **filter_data
    })
    save_all_filters(filters)


# ==========================
# 📦 ХРАНИЛИЩЕ ВСЕХ ФИЛЬТРОВ
# ==========================

def load_all_filters() -> list[dict]:
    if not FILTERS_FILE.exists():
        return []
    with open(FILTERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_all_filters(filters: list[dict]):
    with open(FILTERS_FILE, "w", encoding="utf-8") as f:
        json.dump(filters, f, ensure_ascii=False, indent=2)


def add_filter(new_filter: dict):
    filters = load_all_filters()
    filters.append(new_filter)
    save_all_filters(filters)


def delete_filter(index: int):
    filters = load_all_filters()
    if 0 <= index < len(filters):
        filters.pop(index)
        save_all_filters(filters)


def get_filter(index: int) -> dict | None:
    filters = load_all_filters()
    if 0 <= index < len(filters):
        return filters[index]
    return None
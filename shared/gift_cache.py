import json
from pathlib import Path

def get_cached_models(collection: str) -> dict:
    path = Path("shared/gift_cache.json")
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get("collections", {}).get(collection, {})


def get_cached_collections() -> list:
    path = Path("shared/gift_cache.json")
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return list(data.get("collections", {}).keys())

def get_cached_models_for_collection(collection: str) -> dict:
    return get_cached_models(collection)


# New function to get cached backdrops
def get_cached_backdrops() -> list:
    path = Path("shared/gift_cache.json")
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return list(data.get("backdrops", {}).keys())


# Function to cache backdrops
def cache_backdrops(backdrops: dict):
    path = Path("shared/gift_cache.json")
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}

    data["backdrops"] = backdrops

    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
# Function to cache models for a collection
def cache_models_for_collection(auth_data, collection: str, models: dict):
    path = Path("shared/gift_cache.json")
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}

    if "collections" not in data:
        data["collections"] = {}

    data["collections"][collection] = models

    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
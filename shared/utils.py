import re

def sanitize_filename(s: str) -> str:
    if not s:
        return "none"
    return re.sub(r"[^\w\s\-]", "", s).strip().replace(" ", "_")

def get_filter_filename(collection: str, model: str, backdrop: str, price_limit: float) -> str:
    return f"{sanitize_filename(collection)}_{sanitize_filename(model)}_{sanitize_filename(backdrop)}_{price_limit}.json"

# shared/utils.py

import re
import socket
import json
from loguru import logger


def sanitize_filename(s: str) -> str:
    """🧼 Убираем лишнее из строки и делаем имя файла безопасным"""
    if not s:
        return "none"
    return re.sub(r"[^\w\s\-]", "", s).strip().replace(" ", "_")


def get_filter_filename(collection: str, model: str, backdrop: str, price_limit: float) -> str:
    """📁 Генерим уникальное имя для JSON-файла по фильтру"""
    return f"{sanitize_filename(collection)}_{sanitize_filename(model)}_{sanitize_filename(backdrop)}_{price_limit}.json"


def send_json_to_socket(data: dict):
    """📡 Отправка JSON через TCP-сокет на второй проект"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("127.0.0.1", 9989))  # Порт сокет-сервера во втором проекте
        s.sendall(json.dumps(data).encode())
        s.close()
        logger.success("📤 JSON отправлен через сокет")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки JSON через сокет: {e}")

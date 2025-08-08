from dataclasses import dataclass
from dotenv import load_dotenv
import os

load_dotenv()

@dataclass(frozen=True)
class Settings:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    ALLOWED_USERS: tuple[int, ...] = tuple(
        int(x) for x in os.getenv("ALLOWED_USERS", "").split(",") if x.strip()
    )
    TG_API_ID: int = int(os.getenv("TG_API_ID", "0"))
    TG_API_HASH: str = os.getenv("TG_API_HASH", "")
    SESSION_PATH: str = os.getenv("SESSION_PATH", "./data")
    SESSION_NAME: str = os.getenv("SESSION_NAME", "account")
    DB_DSN: str = os.getenv("DB_DSN", "postgresql://user:pass@localhost:5432/aportals")
    SEARCH_INTERVAL: float = float(os.getenv("SEARCH_INTERVAL", "0.2"))
    SEARCH_LIMIT: int = int(os.getenv("SEARCH_LIMIT", "50"))
    BUY_HOST: str = os.getenv("BUY_HOST", "127.0.0.1")
    BUY_PORT: int = int(os.getenv("BUY_PORT", "8765"))
settings = Settings()

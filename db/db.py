import asyncpg
from config.config import settings

_pool = None

async def get_pool():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(dsn=settings.DB_DSN, min_size=1, max_size=5)
    return _pool

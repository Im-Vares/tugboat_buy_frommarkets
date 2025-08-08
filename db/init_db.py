import asyncio
from pathlib import Path
from db.db import get_pool

async def main():
    sql = Path(__file__).with_name("init.sql").read_text(encoding="utf-8")
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(sql)
    print("DB initialized.")

if __name__ == "__main__":
    asyncio.run(main())

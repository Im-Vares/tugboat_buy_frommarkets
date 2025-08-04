# main.py

import asyncio
from aportals.aportals_handler import init_aportals

async def main():
    await init_aportals()

if __name__ == "__main__":
    asyncio.run(main())
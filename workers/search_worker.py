import asyncio, json
from aportals_api.client import search
from config.config import settings
from db.db_class import DB

db = DB()

async def _send(writer, payload: dict):
    writer.write((json.dumps(payload) + "\n").encode())
    await writer.drain()

def _fits(g, flt) -> bool:
    if g.price > float(flt["max_price"]): return False
    if flt["model"] and (g.model or "").lower() != (flt["model"] or "").lower(): return False
    if flt["backdrop"] and (g.backdrop or "").lower() != (flt["backdrop"] or "").lower(): return False
    return True

async def run_once():
    _, writer = await asyncio.open_connection(settings.BUY_HOST, settings.BUY_PORT)
    filters = await db.filters_active()
    for flt in filters:
        try:
            gifts = await search(
                gift_name=flt["collection"],
                model=flt["model"] or None,
                backdrop=flt["backdrop"] or None,
                min_price=0,
                max_price=float(flt["max_price"]),
                sort="price_asc",
            )
        except Exception as e:
            await db.log("search", "error", "error", filter_id=flt["id"], details=str(e))
            await asyncio.sleep(settings.SEARCH_INTERVAL)
            continue
        for g in gifts:
            if not _fits(g, flt):
                continue
            inserted = await db.add_pending_if_new(g.id, str(g.tg_id), flt["id"], float(g.price))
            if inserted:
                await _send(writer, {
                    "nft_id": g.id, "tg_id": str(g.tg_id),
                    "collection": g.name, "price": float(g.price),
                    "filter_id": flt["id"]
                })
        await asyncio.sleep(settings.SEARCH_INTERVAL)
    writer.close()
    await writer.wait_closed()

async def main():
    while True:
        await run_once()

if __name__ == "__main__":
    asyncio.run(main())

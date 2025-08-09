import asyncio, json, logging
from config.config import settings
from db.db_class import DB
from aportals_api.client import search as api_search

db = DB()
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

def _norm_list(x):
    if x is None: return None
    if isinstance(x, (list, tuple)): return [str(i) for i in x if str(i)]
    return [str(x)]

async def run_once():
    filters = await db.get_active_filters()
    for flt in filters:
        try:
            models = _norm_list(flt.get("model"))
            backs  = _norm_list(flt.get("backdrop"))
            gifts = await api_search(sort="price_asc", offset=0, limit=settings.SEARCH_LIMIT,
                                     gift_name=flt["collection"], model=models, backdrop=backs)
            for g in gifts:
                try:
                    price_ok = float(g.price) <= float(flt["max_price"])
                except Exception:
                    price_ok = False
                if not price_ok:
                    continue
                payload = {
                    "nft_id": getattr(g, "id", None),
                    "price": float(getattr(g, "price", 0)),
                    "collection": getattr(g, "name", ""),
                    "filter_id": flt["id"],
                }
                logging.info("found match: %s", payload)
                await db.log("search", "found", "ok", details=json.dumps(payload))
                await send_to_buy(payload)
        except Exception as e:
            logging.warning("search error for filter %s: %s", flt.get("id"), e)

async def send_to_buy(payload: dict):
    reader, writer = None, None
    try:
        reader, writer = await asyncio.open_connection(settings.BUY_HOST, settings.BUY_PORT)
        writer.write((json.dumps(payload) + "\n").encode())
        await writer.drain()
    finally:
        if writer:
            writer.close()
            await writer.wait_closed()

async def main():
    logging.info('search worker start (interval=%s)', settings.SEARCH_INTERVAL)
    while True:
        await run_once()
        await asyncio.sleep(settings.SEARCH_INTERVAL)

if __name__ == "__main__":
    asyncio.run(main())
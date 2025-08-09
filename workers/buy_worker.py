import asyncio, json, logging
from config.config import settings
from db.db_class import DB
from aportals_api.client import buy as api_buy, my_balances as api_balances

db = DB()
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    addr = writer.get_extra_info('peername')
    logging.info("client connected: %s", addr)
    try:
        while True:
            line = await reader.readline()
            if not line:
                break
            try:
                payload = json.loads(line.decode().strip())
            except Exception as e:
                logging.warning("bad json: %s", e)
                continue

            nft_id = payload.get("nft_id")
            price  = float(payload.get("price", 0))
            if not nft_id or price <= 0:
                logging.warning("invalid payload: %s", payload)
                continue

            # balance
            try:
                balances = await api_balances()
                bal = float(getattr(balances, "balance", 0))
                if bal < price:
                    await db.log("buy", "skip", "no_balance", details=json.dumps({"need": price, "have": bal, "nft_id": nft_id}))
                    logging.warning("no balance: need %.3f, have %.3f", price, bal)
                    continue
            except Exception as e:
                logging.warning("balance check failed: %s", e)

            try:
                await api_buy(nft_id=nft_id, price=price)
                await db.log("buy", "buy", "ok", details=json.dumps(payload))
                logging.info("bought: %s", payload)
            except Exception as e:
                await db.log("buy", "buy", "failed", details=json.dumps({"error": str(e), **payload}))
                logging.warning("buy failed: %s", e)

    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass
        logging.info("client disconnected: %s", addr)

async def main():
    logging.info("Buy server starting on %s:%s", settings.BUY_HOST, settings.BUY_PORT)
    server = await asyncio.start_server(handle_client, settings.BUY_HOST, settings.BUY_PORT)
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
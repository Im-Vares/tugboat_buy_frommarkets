import asyncio, json
from aportals_api.client import buy, my_balances
from config.config import settings
from db.db_class import DB

db = DB()

async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    while not reader.at_eof():
        line = await reader.readline()
        if not line:
            break
        try:
            msg = json.loads(line.decode())
            nft_id = msg["nft_id"]
            price = float(msg["price"])
            status = await db.pending_status(nft_id)
            if status != "pending":
                continue
            b = await my_balances()
            if float(b.balance) < price:
                await db.set_status(nft_id, "no_balance")
                await db.log("buy", "precheck", "skip", gift_id=nft_id, price=price, details="insufficient_balance")
                continue
            try:
                await buy(nft_id=nft_id, price=price)
                await db.set_status(nft_id, "bought")
                await db.log("buy", "buy", "ok", gift_id=nft_id, price=price)
            except Exception as e:
                await db.set_status(nft_id, "failed")
                await db.log("buy", "buy", "error", gift_id=nft_id, price=price, details=str(e))
        except Exception as e:
            await db.log("buy", "parse", "error", details=str(e))
    writer.close()
    await writer.wait_closed()

async def main():
    server = await asyncio.start_server(handle_client, settings.BUY_HOST, settings.BUY_PORT)
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())

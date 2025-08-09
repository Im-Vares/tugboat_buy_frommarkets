from typing import Optional, Sequence, Dict, Any
from db.db import get_pool

class DB:
    async def filters_active(self) -> Sequence[Dict[str, Any]]:
        pool = await get_pool()
        rows = await pool.fetch("SELECT * FROM filters WHERE active = TRUE ORDER BY id DESC")
        return [dict(r) for r in rows]

    async def add_pending_if_new(self, gift_id: str, tg_id: str, filter_id: int, price: float) -> bool:
        pool = await get_pool()
        res = await pool.execute(
            """INSERT INTO pending_gifts(gift_id, tg_id, filter_id, price, status)
                   VALUES($1,$2,$3,$4,'pending')
                   ON CONFLICT (gift_id) DO NOTHING""",  # noqa
            gift_id, tg_id, filter_id, price
        )
        return res == "INSERT 0 1"

    async def pending_status(self, gift_id: str) -> Optional[str]:
        pool = await get_pool()
        row = await pool.fetchrow("SELECT status FROM pending_gifts WHERE gift_id=$1", gift_id)
        return row["status"] if row else None

    async def set_status(self, gift_id: str, status: str):
        pool = await get_pool()
        await pool.execute("UPDATE pending_gifts SET status=$2 WHERE gift_id=$1", gift_id, status)

    async def log(self, source: str, action: str, result: str, **kw):
        pool = await get_pool()
        await pool.execute(
            "INSERT INTO logs(source, action, gift_id, filter_id, user_id, price, result, details) "
            "VALUES($1,$2,$3,$4,$5,$6,$7,$8)",
            source, action, kw.get("gift_id"), kw.get("filter_id"),
            kw.get("user_id"), kw.get("price"), result, kw.get("details"),
        )
    async def add_filter(self, user_id: int, collection: str, model, backdrop, max_price: float, quantity: int, active: bool=True) -> int:
        pool = await get_pool()
        row = await pool.fetchrow(
            "INSERT INTO filters(user_id, collection, model, backdrop, max_price, quantity, active) VALUES($1,$2,$3,$4,$5,$6,$7) RETURNING id",
            user_id, collection, model, backdrop, max_price, quantity, active
        )
        return row["id"]
    async def delete_filter(self, fid: int) -> None:
        pool = await get_pool()
        await pool.execute("DELETE FROM filters WHERE id=$1", fid)
    async def get_active_filters(self):
        pool = await get_pool()
        rows = await pool.fetch("SELECT * FROM filters WHERE active = TRUE ORDER BY id DESC")
        return [dict(r) for r in rows]

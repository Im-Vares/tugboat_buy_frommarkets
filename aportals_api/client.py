from typing import Optional
from aportalsmp.auth import update_auth
from aportalsmp.gifts import search as _search, buy as _buy
from aportalsmp.gifts import collections as _collections, filterFloors as _filterFloors
from aportalsmp.account import myBalances as _myBalances
from config.config import settings

_auth_cache: Optional[str] = None

async def get_auth() -> str:
    global _auth_cache
    if _auth_cache:
        return _auth_cache
    _auth_cache = await update_auth(
        api_id=settings.TG_API_ID,
        api_hash=settings.TG_API_HASH,
        session_path=settings.SESSION_PATH,
        session_name=settings.SESSION_NAME,
    )
    return _auth_cache

async def search(**kwargs):
    kwargs.setdefault("sort", "price_asc")
    kwargs.setdefault("offset", 0)
    kwargs.setdefault("limit", settings.SEARCH_LIMIT)
    kwargs["authData"] = await get_auth()
    return await _search(**kwargs)

async def buy(nft_id: str, price: float):
    return await _buy(nft_id=nft_id, price=price, authData=await get_auth())

async def collections(limit: int = 0):
    return await _collections(limit=limit, authData=await get_auth())

async def filter_floors(gift_name: str):
    return await _filterFloors(gift_name=gift_name, authData=await get_auth())

async def my_balances():
    return await _myBalances(authData=await get_auth())

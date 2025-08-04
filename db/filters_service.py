from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from db.models import Filter, PendingGift
from pathlib import Path
import re


def sanitize_filename(s: str) -> str:
    return re.sub(r"[^\w\s\-]", "", s or "").strip().replace(" ", "_") or "none"


def get_filter_filename(collection: str, model: str, backdrop: str, price_limit: float) -> str:
    return f"{sanitize_filename(collection)}_{sanitize_filename(model)}_{sanitize_filename(backdrop)}_{price_limit}.json"


async def save_filter(session: AsyncSession, data: dict, user_id: int) -> Filter:
    new_filter = Filter(**data, user_id=user_id)
    session.add(new_filter)
    await session.commit()
    await session.refresh(new_filter)
    return new_filter


async def get_filters(session: AsyncSession, user_id: int | None = None) -> list[Filter]:
    query = select(Filter)
    if user_id is not None:
        query = query.where(Filter.user_id == user_id)

    result = await session.execute(query)
    return result.scalars().all()


async def delete_filter(session: AsyncSession, filter_id: int, user_id: int) -> bool:
    result = await session.execute(
        select(Filter).where(Filter.id == filter_id, Filter.user_id == user_id)
    )
    f = result.scalar_one_or_none()
    if f:
        # 1. Удаляем связанные pending_gifts
        await session.execute(
            delete(PendingGift).where(PendingGift.filter_id == filter_id)
        )

        # 2. Удаляем сам фильтр
        await session.delete(f)
        await session.commit()

        # 3. Удаляем JSON-файл, если он есть
        filename = get_filter_filename(f.collection, f.model, f.backdrop, f.price_limit)
        filepath = Path("data") / filename
        if filepath.exists():
            filepath.unlink()

        return True
    return False
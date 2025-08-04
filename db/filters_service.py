from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from db.models import Filter, PendingGift


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
        return True
    return False
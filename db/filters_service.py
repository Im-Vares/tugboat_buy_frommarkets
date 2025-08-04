from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import Filter


async def save_filter(session: AsyncSession, data: dict, user_id: int) -> Filter:
    new_filter = Filter(**data, user_id=user_id)
    session.add(new_filter)
    await session.commit()
    await session.refresh(new_filter)
    return new_filter


async def get_filters(session: AsyncSession, user_id: int) -> list[Filter]:
    result = await session.execute(select(Filter).where(Filter.user_id == user_id))
    return result.scalars().all()


async def delete_filter(session: AsyncSession, filter_id: int, user_id: int) -> bool:
    result = await session.execute(
        select(Filter).where(Filter.id == filter_id, Filter.user_id == user_id)
    )
    f = result.scalar_one_or_none()
    if f:
        await session.delete(f)
        await session.commit()
        return True
    return False
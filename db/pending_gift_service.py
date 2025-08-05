from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from db.models import PendingGift


async def save_pending_gift(session: AsyncSession, filter_id: int, gift: dict):
    pending = PendingGift(
        filter_id=filter_id,
        gift_json=gift,
        status="pending"
    )
    session.add(pending)
    await session.commit()
    await session.refresh(pending)
    return pending


async def get_pending_gifts(session: AsyncSession, filter_id: int):
    result = await session.execute(
        select(PendingGift).where(
            PendingGift.filter_id == filter_id,
            PendingGift.status == "pending"
        )
    )
    return result.scalars().all()


async def mark_gift_as_sent(session: AsyncSession, gift_id: int):
    await session.execute(
        update(PendingGift)
        .where(PendingGift.id == gift_id)
        .values(status="sent")
    )
    await session.commit()


async def is_gift_already_pending(session: AsyncSession, filter_id: int, gift_id: str) -> bool:
    result = await session.execute(
        select(PendingGift)
        .where(PendingGift.filter_id == filter_id)
        .where(PendingGift.gift_json["id"].as_string() == gift_id)
    )
    return result.scalar_one_or_none() is not None


async def delete_pending_gifts_by_filter(session: AsyncSession, filter_id: int):
    await session.execute(
        delete(PendingGift).where(PendingGift.filter_id == filter_id)
    )
    await session.commit()
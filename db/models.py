from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, mapped_column, relationship
from sqlalchemy import Integer, String, Float, BigInteger, ForeignKey, JSON, DateTime


class Base(DeclarativeBase):
    pass


class Filter(Base):
    __tablename__ = "filters"

    id = mapped_column(Integer, primary_key=True)
    user_id = mapped_column(BigInteger, nullable=False)

    collection = mapped_column(String, nullable=False)
    model = mapped_column(String, nullable=True)
    backdrop = mapped_column(String, nullable=True)
    symbol = mapped_column(String, nullable=True)

    price_limit = mapped_column(Float, nullable=False)


class PendingGift(Base):
    __tablename__ = "pending_gifts"

    id = mapped_column(Integer, primary_key=True)
    filter_id = mapped_column(Integer, ForeignKey("filters.id"), nullable=False)

    gift_json = mapped_column(JSON, nullable=False)
    status = mapped_column(String, default="pending")
    created_at = mapped_column(DateTime, default=datetime.utcnow)

    filter = relationship("Filter", backref="pending_gifts")
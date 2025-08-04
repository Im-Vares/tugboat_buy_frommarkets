from sqlalchemy.orm import DeclarativeBase, mapped_column
from sqlalchemy import Integer, String, Float, BigInteger


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
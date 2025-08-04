# db/models.py
from sqlalchemy import Column, Integer, String, Float
from db.db import Base

class Filter(Base):
    __tablename__ = "filters"

    id = Column(Integer, primary_key=True, index=True)
    collection = Column(String, nullable=False)
    model = Column(String, nullable=True)
    backdrop = Column(String, nullable=True)
    symbol = Column(String, nullable=True)
    price_limit = Column(Float, nullable=False)
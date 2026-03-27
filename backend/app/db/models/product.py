from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String
from sqlalchemy.types import JSON

from app.db.db_config import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False, default=0.0)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)

    sizes = Column(JSON, nullable=False, default=list)
    colors = Column(JSON, nullable=False, default=list)
    style_tags = Column(JSON, nullable=False, default=list)
    scenarios = Column(JSON, nullable=False, default=list)
    images = Column(JSON, nullable=False, default=list)

    stock = Column(Boolean, nullable=False, default=True)

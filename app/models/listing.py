from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class EtsyListing(Base):
    __tablename__ = "etsy_listings"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(String(5000), nullable=True)
    tags = Column(JSON, nullable=True, default=list)
    price = Column(Float, nullable=False, default=0.0)
    status = Column(String(20), nullable=False, default="draft")  # draft, active, inactive, sold_out
    etsy_id = Column(String(100), nullable=True, unique=True)
    views = Column(Integer, default=0)
    favourites = Column(Integer, default=0)
    sales = Column(Integer, default=0)
    revenue = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

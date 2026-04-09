from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)   # planner, printable, wall_art, journal, checklist, invitation
    niche = Column(String(100), nullable=False)
    stage = Column(String(20), nullable=False, default="draft", index=True)  # draft, review, approved, listed, live
    file_path = Column(String(500), nullable=True)
    etsy_listing_id = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

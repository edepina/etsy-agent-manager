from sqlalchemy import Column, Integer, Date, Float
from sqlalchemy.sql import func
from app.database import Base


class DailyMetric(Base):
    __tablename__ = "daily_metrics"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, unique=True, index=True)
    total_products = Column(Integer, default=0)
    total_sales = Column(Integer, default=0)
    total_revenue = Column(Float, default=0.0)
    total_views = Column(Integer, default=0)
    agent_runs = Column(Integer, default=0)
    agent_costs = Column(Float, default=0.0)

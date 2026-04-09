import random
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import BaseAgent


class AnalyticsAgent(BaseAgent):
    """Pulls Etsy shop stats and updates daily metrics.
    
    Currently: generates mock metrics.
    Future: Etsy API v3 stats endpoints via EtsyService.
    """

    agent_type = "analytics"

    async def run(self, input_data: dict, db: AsyncSession) -> dict:
        today = date.today()

        daily_stats = []
        for i in range(7):
            day = today - timedelta(days=i)
            daily_stats.append({
                "date": day.isoformat(),
                "views": random.randint(10, 200),
                "sales": random.randint(0, 10),
                "revenue": round(random.uniform(0, 50), 2),
                "favourites": random.randint(0, 20),
            })

        top_products = [
            {"product_id": random.randint(1, 20), "sales": random.randint(1, 30), "revenue": round(random.uniform(5, 150), 2)}
            for _ in range(5)
        ]

        return {
            "period": "last_7_days",
            "total_views": sum(d["views"] for d in daily_stats),
            "total_sales": sum(d["sales"] for d in daily_stats),
            "total_revenue": round(sum(d["revenue"] for d in daily_stats), 2),
            "daily_stats": daily_stats,
            "top_products": top_products,
            "tokens_used": 0,
            "cost": 0.0,
        }

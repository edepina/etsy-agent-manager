import random
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import BaseAgent


class ResearchAgent(BaseAgent):
    """Researches Etsy market opportunities for Islamic digital products.
    
    Currently: generates mock opportunity data.
    Future: Etsy API scraping + Claude analysis of trending niches.
    """

    agent_type = "research"

    NICHES = [
        "Ramadan Planner",
        "Islamic Wall Art",
        "Eid Invitation",
        "Quran Journal",
        "Prayer Tracker",
        "Hijri Calendar",
        "Dua Checklist",
        "Islamic Kids Activity",
        "Nikah Invitation",
        "Hajj Planner",
    ]

    PRODUCT_TYPES = ["planner", "printable", "wall_art", "journal", "checklist", "invitation"]

    async def run(self, input_data: dict, db: AsyncSession) -> dict:
        opportunities = []
        for _ in range(5):
            niche = random.choice(self.NICHES)
            product_type = random.choice(self.PRODUCT_TYPES)
            opportunities.append({
                "niche": niche,
                "product_type": product_type,
                "estimated_demand": random.randint(50, 500),
                "competition_score": round(random.uniform(0.1, 0.9), 2),
                "opportunity_score": round(random.uniform(0.5, 1.0), 2),
                "suggested_price": round(random.uniform(2.99, 9.99), 2),
                "keywords": [niche.lower(), product_type, "islamic", "printable", "digital download"],
                "discovered_at": datetime.now(timezone.utc).isoformat(),
            })

        opportunities.sort(key=lambda x: x["opportunity_score"], reverse=True)

        return {
            "opportunities": opportunities,
            "total_found": len(opportunities),
            "tokens_used": 0,
            "cost": 0.0,
        }

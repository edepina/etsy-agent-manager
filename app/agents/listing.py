import random
import string
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import BaseAgent


class ListingAgent(BaseAgent):
    """Creates Etsy listings for approved products.
    
    Currently: generates mock listing data.
    Future: Etsy API v3 integration via EtsyService.
    """

    agent_type = "listing"

    async def run(self, input_data: dict, db: AsyncSession) -> dict:
        title = input_data.get("title", "Islamic Printable")
        description = input_data.get("description", "")
        tags = input_data.get("tags", [])
        price = input_data.get("price", 4.99)

        mock_etsy_id = "".join(random.choices(string.digits, k=10))

        return {
            "etsy_listing_id": mock_etsy_id,
            "etsy_url": f"https://www.etsy.com/listing/{mock_etsy_id}",
            "title": title,
            "price": price,
            "status": "active",
            "tags_published": tags[:13],
            "tokens_used": 0,
            "cost": 0.0,
        }

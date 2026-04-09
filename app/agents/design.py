import os
import random
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import BaseAgent


class DesignAgent(BaseAgent):
    """Generates PDF/image files for Islamic digital products.
    
    Currently: creates mock file references.
    Future: WeasyPrint or ReportLab PDF generation, Pillow for images.
    """

    agent_type = "design"

    async def run(self, input_data: dict, db: AsyncSession) -> dict:
        niche = input_data.get("niche", "Islamic Planner")
        product_type = input_data.get("product_type", "planner")
        product_id = input_data.get("product_id", random.randint(1000, 9999))

        slug = niche.lower().replace(" ", "-")
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        filename = f"products/{slug}-{product_type}-{product_id}-{timestamp}.pdf"

        mock_pages = random.randint(4, 52)

        return {
            "file_path": filename,
            "format": "PDF",
            "pages": mock_pages,
            "dimensions": "A4 + US Letter",
            "file_size_kb": mock_pages * random.randint(80, 200),
            "thumbnail_path": filename.replace(".pdf", "-thumb.png"),
            "tokens_used": 0,
            "cost": 0.0,
        }

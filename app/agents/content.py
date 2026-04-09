import random
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import BaseAgent


class ContentAgent(BaseAgent):
    """Generates Etsy listing content for Islamic digital products.
    
    Currently: generates mock product content.
    Future: Claude API for SEO-optimised titles, descriptions, and tags.
    """

    agent_type = "content"

    TITLE_TEMPLATES = [
        "{niche} | Islamic Printable | Digital Download | Instant Download",
        "Beautiful {niche} | Muslim Gift | {product_type} | PDF Printable",
        "{niche} Printable | Islamic Digital Product | Instant Download PDF",
        "Ramadan {niche} | Islamic {product_type} | Digital Download",
    ]

    async def run(self, input_data: dict, db: AsyncSession) -> dict:
        niche = input_data.get("niche", "Islamic Planner")
        product_type = input_data.get("product_type", "planner")
        price = input_data.get("suggested_price", 4.99)

        title = random.choice(self.TITLE_TEMPLATES).format(
            niche=niche, product_type=product_type.replace("_", " ").title()
        )

        description = (
            f"✨ {niche} — Beautifully designed Islamic {product_type.replace('_', ' ')} "
            f"to help you organise your spiritual journey.\n\n"
            f"📥 INSTANT DOWNLOAD — receive your files immediately after purchase.\n\n"
            f"📄 WHAT'S INCLUDED:\n"
            f"• High-resolution PDF (A4 + US Letter)\n"
            f"• Print-ready files\n\n"
            f"🖨️ PRINTING TIPS:\n"
            f"Print at home or at your local print shop for best results.\n\n"
            f"💌 PLEASE NOTE:\n"
            f"This is a digital download. No physical item will be shipped.\n\n"
            f"Jazakallah Khayran for your support! 🌙"
        )

        tags = [
            niche.lower(),
            "islamic printable",
            "muslim gift",
            "digital download",
            "instant download",
            product_type.replace("_", " "),
            "ramadan gift",
            "eid gift",
            "islamic art",
            "halal planner",
            "muslim planner",
            "quran journal",
            "prayer tracker",
        ][:13]

        return {
            "title": title,
            "description": description,
            "tags": tags,
            "price": price,
            "tokens_used": 0,
            "cost": 0.0,
        }

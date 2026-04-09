import logging
from enum import Enum
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.agents.base import BaseAgent
from app.agents.research import ResearchAgent
from app.agents.content import ContentAgent
from app.agents.design import DesignAgent
from app.agents.listing import ListingAgent
from app.models.product import Product

logger = logging.getLogger(__name__)


class PipelineStage(str, Enum):
    RESEARCH = "research"
    CONTENT = "content"
    DESIGN = "design"
    REVIEW = "review"
    LISTING = "listing"
    MONITOR = "monitor"


class MasterController(BaseAgent):
    """Orchestrates the full pipeline: RESEARCH → CONTENT → DESIGN → REVIEW → LISTING → MONITOR.
    
    Manages workflow state machine, triggers sub-agents, handles failures/retries.
    The REVIEW stage pauses the pipeline and waits for human approval via the dashboard.
    """

    agent_type = "master"

    def __init__(self):
        super().__init__()
        self.research_agent = ResearchAgent()
        self.content_agent = ContentAgent()
        self.design_agent = DesignAgent()
        self.listing_agent = ListingAgent()

    async def run(self, input_data: dict, db: AsyncSession) -> dict:
        stage = input_data.get("start_stage", PipelineStage.RESEARCH)
        results = {}

        if stage == PipelineStage.RESEARCH:
            logger.info("Pipeline: RESEARCH stage")
            research_result = await self.research_agent.execute(input_data, db)
            results["research"] = research_result
            opportunities = research_result.get("opportunities", [])
            if not opportunities:
                return {**results, "status": "no_opportunities", "tokens_used": 0, "cost": 0.0}

            top_opportunity = opportunities[0]
            stage = PipelineStage.CONTENT
            input_data = {**input_data, **top_opportunity}

        if stage == PipelineStage.CONTENT:
            logger.info("Pipeline: CONTENT stage")
            content_result = await self.content_agent.execute(input_data, db)
            results["content"] = content_result
            input_data = {**input_data, **content_result}
            stage = PipelineStage.DESIGN

        if stage == PipelineStage.DESIGN:
            logger.info("Pipeline: DESIGN stage")
            design_result = await self.design_agent.execute(input_data, db)
            results["design"] = design_result
            input_data = {**input_data, **design_result}

            product = Product(
                name=input_data.get("title", input_data.get("niche", "New Product")),
                type=input_data.get("product_type", "printable"),
                niche=input_data.get("niche", "Islamic"),
                stage="review",
                file_path=design_result.get("file_path"),
                description=input_data.get("description"),
            )
            db.add(product)
            await db.flush()
            results["product_id"] = product.id
            results["stage"] = PipelineStage.REVIEW
            logger.info(f"Pipeline: PAUSED at REVIEW for product {product.id}")
            return {
                **results,
                "status": "awaiting_review",
                "message": "Product created and awaiting human review",
                "tokens_used": 0,
                "cost": 0.0,
            }

        return {**results, "status": "completed", "tokens_used": 0, "cost": 0.0}

    async def resume_after_approval(self, product_id: int, listing_data: dict, db: AsyncSession) -> dict:
        logger.info(f"Pipeline: LISTING stage for product {product_id}")
        listing_result = await self.listing_agent.execute(listing_data, db)

        await db.execute(
            update(Product)
            .where(Product.id == product_id)
            .values(stage="listed", etsy_listing_id=listing_result.get("etsy_listing_id"))
        )

        return {
            "product_id": product_id,
            "listing": listing_result,
            "status": "listed",
            "tokens_used": 0,
            "cost": 0.0,
        }

"""Research Agent — searches Etsy for Islamic digital product opportunities and analyses them via Claude."""

import json
import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.agents.base import BaseAgent
from app.models.research import ResearchNiche, ResearchResult
from app.services.etsy import EtsyService, EtsyAPIError, compute_top_tags

logger = logging.getLogger(__name__)

ANALYSIS_PROMPT = """You are a market research analyst specialising in Etsy digital products, specifically Islamic digital products (planners, printables, wall art, journals).

I've collected data from Etsy for the niche: "{niche_name}"

Here is the market data:
- Total active listings found: {total_listings}
- Price range: ${min_price} — ${max_price} (average: ${avg_price})
- Average views per listing: {avg_views}
- Average favourites per listing: {avg_favourites}
- Most common tags: {top_tags}

Top performing listings (by relevance score):
{top_listings_formatted}

Based on this data, provide your analysis in the following JSON format:
{{
    "opportunity_score": <0-100, where 100 is highest opportunity>,
    "competition_level": "<low|medium|high>",
    "demand_signal": "<low|medium|high>",
    "analysis_summary": "<2-3 paragraph analysis of the niche opportunity, mentioning specific gaps, pricing strategies, and what makes top listings succeed>",
    "suggested_products": [
        {{
            "name": "<specific product idea>",
            "type": "<planner|journal|wall_art|printable|checklist|invitation|worksheet>",
            "estimated_price": <suggested price in USD>,
            "reasoning": "<why this would sell>"
        }}
    ],
    "gaps_identified": [
        "<specific gap in the market, e.g. 'No bilingual Arabic/English Ramadan planners with tashkeel'>"
    ]
}}

Important considerations:
- We specialise in authentic Islamic content with proper Arabic text and tashkeel
- Our competitive advantage is Islamic scholarly knowledge (accurate hadith references, correct du'a text)
- Prioritise products where quality/authenticity is a differentiator
- Flag any niches that are oversaturated
- Consider seasonal timing (Ramadan, Hajj season, Eid, Muharram, etc.)

Respond ONLY with the JSON object, no additional text."""


def _format_top_listings(listings: list[dict], top_n: int = 10) -> str:
    """Format top listings for the Claude prompt."""
    lines = []
    for i, listing in enumerate(listings[:top_n], 1):
        price = listing.get("price", {})
        amount = price.get("amount", 0) / max(price.get("divisor", 100), 1) if isinstance(price, dict) else 0
        lines.append(
            f"{i}. \"{listing.get('title', 'N/A')[:80]}\" "
            f"— ${amount:.2f}, {listing.get('views', 0)} views, "
            f"{listing.get('num_favorers', 0)} favs"
        )
    return "\n".join(lines) if lines else "No listings data available."


def _compute_stats(listings: list[dict]) -> dict:
    """Compute aggregate stats from a list of Etsy listings."""
    if not listings:
        return {"avg_price": 0.0, "min_price": 0.0, "max_price": 0.0, "avg_views": 0, "avg_favourites": 0}

    prices = []
    for listing in listings:
        price = listing.get("price", {})
        if isinstance(price, dict) and price.get("divisor", 0):
            prices.append(price["amount"] / price["divisor"])

    views = [listing.get("views", 0) for listing in listings]
    favs = [listing.get("num_favorers", 0) for listing in listings]

    return {
        "avg_price": round(sum(prices) / len(prices), 2) if prices else 0.0,
        "min_price": round(min(prices), 2) if prices else 0.0,
        "max_price": round(max(prices), 2) if prices else 0.0,
        "avg_views": int(sum(views) / len(views)) if views else 0,
        "avg_favourites": int(sum(favs) / len(favs)) if favs else 0,
    }


def _sample_listings(listings: list[dict], top_n: int = 10) -> list[dict]:
    """Extract key fields from top listings for storage."""
    result = []
    for listing in listings[:top_n]:
        price = listing.get("price", {})
        amount = price.get("amount", 0) / max(price.get("divisor", 100), 1) if isinstance(price, dict) else 0
        result.append({
            "listing_id": listing.get("listing_id"),
            "title": listing.get("title", "")[:120],
            "price": round(amount, 2),
            "views": listing.get("views", 0),
            "num_favorers": listing.get("num_favorers", 0),
            "tags": listing.get("tags", [])[:10],
            "url": listing.get("url", ""),
            "shop_id": listing.get("shop_id"),
        })
    return result


class ResearchAgent(BaseAgent):
    """Researches Etsy market opportunities for Islamic digital products.

    For each enabled ResearchNiche:
    1. Calls EtsyService.search_niche() to collect listing data
    2. Computes aggregate stats
    3. Sends data to Claude for opportunity analysis
    4. Stores ResearchResult in the database

    Falls back gracefully if Etsy API returns 403 (key pending approval)
    or if Claude analysis fails.
    """

    agent_type = "research"

    async def run(self, input_data: dict, db: AsyncSession) -> dict:
        """Run research for all enabled niches (or specific niche_ids if provided)."""
        import anthropic
        from app.config import settings

        niche_ids: list[int] | None = input_data.get("niche_ids")

        query = select(ResearchNiche).where(ResearchNiche.enabled == True)  # noqa: E712
        if niche_ids:
            query = query.where(ResearchNiche.id.in_(niche_ids))
        niches = (await db.execute(query)).scalars().all()

        if not niches:
            logger.warning("ResearchAgent: no enabled niches found")
            self.report_progress(
                {
                    "phase": "complete",
                    "current": 0,
                    "total": 0,
                    "progress_percent": 100,
                    "message": "No enabled niches found",
                }
            )
            return {"niches_processed": 0, "tokens_used": 0, "cost": 0.0}

        etsy = EtsyService()
        claude = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

        total_tokens = 0
        total_cost = 0.0
        results_summary = []
        etsy_available = True

        total_niches = len(niches)

        for index, niche in enumerate(niches, start=1):
            progress_percent = int(((index - 1) / total_niches) * 100)
            self.report_progress(
                {
                    "phase": "running",
                    "current": index - 1,
                    "total": total_niches,
                    "progress_percent": progress_percent,
                    "niche": niche.name,
                    "message": f"Processing niche {index}/{total_niches}: {niche.name}",
                }
            )

            logger.info("ResearchAgent: processing niche '%s'", niche.name)
            listings: list[dict] = []

            # --- Etsy data collection ---
            if etsy_available:
                try:
                    listings = await etsy.search_niche(
                        niche_keywords=niche.keywords,
                        max_results=200,
                    )
                    logger.info(
                        "ResearchAgent: niche '%s' — %d listings found", niche.name, len(listings)
                    )
                except EtsyAPIError as exc:
                    if exc.status_code == 403:
                        logger.warning(
                            "ResearchAgent: Etsy API key not yet approved (403) — "
                            "storing pending_analysis result for '%s'", niche.name
                        )
                        etsy_available = False
                    else:
                        logger.error(
                            "ResearchAgent: Etsy error for niche '%s': %s", niche.name, exc
                        )
                    listings = []

            stats = _compute_stats(listings)
            top_tags = compute_top_tags(listings)
            sample = _sample_listings(listings)

            # --- Claude analysis ---
            analysis_status = "complete"
            opportunity_score = 0
            competition_level = "unknown"
            demand_signal = "unknown"
            analysis_summary = ""
            suggested_products: list = []
            gaps_identified: list = []
            input_tokens = 0
            output_tokens = 0

            if not listings:
                analysis_status = "pending_analysis" if not etsy_available else "error"
            else:
                try:
                    prompt = ANALYSIS_PROMPT.format(
                        niche_name=niche.name,
                        total_listings=len(listings),
                        min_price=stats["min_price"],
                        max_price=stats["max_price"],
                        avg_price=stats["avg_price"],
                        avg_views=stats["avg_views"],
                        avg_favourites=stats["avg_favourites"],
                        top_tags=", ".join(top_tags[:20]),
                        top_listings_formatted=_format_top_listings(listings),
                    )

                    message = await claude.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=2000,
                        messages=[{"role": "user", "content": prompt}],
                    )

                    input_tokens = message.usage.input_tokens
                    output_tokens = message.usage.output_tokens
                    # Claude Sonnet pricing approximation
                    call_cost = (input_tokens * 3 + output_tokens * 15) / 1_000_000
                    total_tokens += input_tokens + output_tokens
                    total_cost += call_cost

                    raw_text = message.content[0].text.strip()
                    try:
                        parsed = json.loads(raw_text)
                        opportunity_score = int(parsed.get("opportunity_score", 0))
                        competition_level = parsed.get("competition_level", "unknown")
                        demand_signal = parsed.get("demand_signal", "unknown")
                        analysis_summary = parsed.get("analysis_summary", "")
                        suggested_products = parsed.get("suggested_products", [])
                        gaps_identified = parsed.get("gaps_identified", [])
                    except (json.JSONDecodeError, ValueError) as parse_err:
                        logger.error(
                            "ResearchAgent: failed to parse Claude JSON for '%s': %s",
                            niche.name, parse_err,
                        )
                        analysis_status = "error"
                        analysis_summary = raw_text[:500]

                except Exception as claude_err:
                    logger.error(
                        "ResearchAgent: Claude failed for niche '%s': %s", niche.name, claude_err
                    )
                    analysis_status = "pending_analysis"

            # --- Store result ---
            result = ResearchResult(
                niche_id=niche.id,
                total_listings_found=len(listings),
                avg_price=stats["avg_price"],
                min_price=stats["min_price"],
                max_price=stats["max_price"],
                avg_views=stats["avg_views"],
                avg_favourites=stats["avg_favourites"],
                top_tags=top_tags,
                sample_listings=sample,
                opportunity_score=opportunity_score,
                competition_level=competition_level,
                demand_signal=demand_signal,
                analysis_summary=analysis_summary,
                suggested_products=suggested_products,
                gaps_identified=gaps_identified,
                analysis_status=analysis_status,
                created_at=datetime.now(timezone.utc),
            )
            db.add(result)
            await db.flush()

            results_summary.append({
                "niche": niche.name,
                "listings_found": len(listings),
                "opportunity_score": opportunity_score,
                "analysis_status": analysis_status,
            })
            logger.info(
                "ResearchAgent: '%s' stored — score=%d status=%s",
                niche.name, opportunity_score, analysis_status,
            )

            self.report_progress(
                {
                    "phase": "running",
                    "current": index,
                    "total": total_niches,
                    "progress_percent": int((index / total_niches) * 100),
                    "niche": niche.name,
                    "message": f"Completed niche {index}/{total_niches}: {niche.name}",
                }
            )

        await etsy.aclose()

        self.report_progress(
            {
                "phase": "complete",
                "current": total_niches,
                "total": total_niches,
                "progress_percent": 100,
                "message": "Research run complete",
            }
        )

        return {
            "niches_processed": len(niches),
            "results": results_summary,
            "etsy_available": etsy_available,
            "tokens_used": total_tokens,
            "cost": round(total_cost, 6),
        }

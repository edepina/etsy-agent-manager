"""Research dashboard routes."""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.database import get_db
from app.models.research import ResearchNiche, ResearchResult
from app.auth import login_required, generate_csrf_token

router = APIRouter(prefix="/research")
templates = Jinja2Templates(directory="app/templates")


@router.get("")
async def research_overview(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: str = Depends(login_required),
):
    """Research results overview page."""
    niches = (
        await db.execute(select(ResearchNiche).order_by(ResearchNiche.name))
    ).scalars().all()

    # Latest result per niche
    niche_rows = []
    top_result = None
    for niche in niches:
        latest = await db.scalar(
            select(ResearchResult)
            .where(ResearchResult.niche_id == niche.id)
            .order_by(desc(ResearchResult.created_at))
            .limit(1)
        )
        niche_rows.append({"niche": niche, "latest": latest})
        if latest and (top_result is None or latest.opportunity_score > top_result.opportunity_score):
            top_result = latest

    total_niches = len(niches)
    enabled_niches = sum(1 for n in niches if n.enabled)

    last_run = await db.scalar(
        select(ResearchResult).order_by(desc(ResearchResult.created_at)).limit(1)
    )

    return templates.TemplateResponse(
        "research.html",
        {
            "request": request,
            "niche_rows": niche_rows,
            "top_result": top_result,
            "total_niches": total_niches,
            "enabled_niches": enabled_niches,
            "last_run": last_run,
            "active_page": "research",
            "csrf_token": generate_csrf_token(request),
        },
    )


@router.get("/{niche_id}")
async def research_detail(
    request: Request,
    niche_id: int,
    db: AsyncSession = Depends(get_db),
    user: str = Depends(login_required),
):
    """Detailed view for a single niche with history."""
    niche = await db.get(ResearchNiche, niche_id)
    if not niche:
        raise HTTPException(status_code=404, detail="Niche not found")

    results = (
        await db.execute(
            select(ResearchResult)
            .where(ResearchResult.niche_id == niche_id)
            .order_by(desc(ResearchResult.created_at))
            .limit(20)
        )
    ).scalars().all()

    latest = results[0] if results else None

    # History for ApexCharts (oldest → newest)
    history = list(reversed(results))
    chart_labels = [r.created_at.strftime("%b %d") if r.created_at else "" for r in history]
    chart_scores = [r.opportunity_score for r in history]

    return templates.TemplateResponse(
        "research_detail.html",
        {
            "request": request,
            "niche": niche,
            "latest": latest,
            "results": results,
            "chart_labels": chart_labels,
            "chart_scores": chart_scores,
            "active_page": "research",
            "csrf_token": generate_csrf_token(request),
        },
    )

from typing import Optional

from fastapi import APIRouter, Request, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_db
from app.models.agent import AgentRun
from app.models.product import Product
from app.models.metric import DailyMetric
from app.models.research import ResearchNiche, ResearchResult
from app.auth import api_login_required

router = APIRouter(prefix="/api")
limiter = Limiter(key_func=get_remote_address)


@router.get("/agents/status")
@limiter.limit("60/minute")
async def get_agent_status(request: Request, db: AsyncSession = Depends(get_db), user: str = Depends(api_login_required)):
    agent_types = ["research", "content", "design", "listing", "analytics"]
    statuses = {}

    for agent_type in agent_types:
        last_run = await db.execute(
            select(AgentRun)
            .where(AgentRun.agent_type == agent_type)
            .order_by(desc(AgentRun.started_at))
            .limit(1)
        )
        last_run = last_run.scalars().first()

        statuses[agent_type] = {
            "status": last_run.status if last_run else "idle",
            "last_run": last_run.started_at.isoformat() if last_run and last_run.started_at else None,
            "last_error": last_run.error if last_run else None,
        }

    pending_reviews = await db.scalar(
        select(func.count(Product.id)).where(Product.stage == "review")
    ) or 0

    return {"agents": statuses, "pending_reviews": pending_reviews}


@router.get("/dashboard/stats")
@limiter.limit("60/minute")
async def get_dashboard_stats(request: Request, db: AsyncSession = Depends(get_db), user: str = Depends(api_login_required)):
    total_products = await db.scalar(select(func.count(Product.id))) or 0
    pending_reviews = await db.scalar(
        select(func.count(Product.id)).where(Product.stage == "review")
    ) or 0

    result = await db.execute(
        select(DailyMetric).order_by(desc(DailyMetric.date)).limit(30)
    )
    metrics = result.scalars().all()
    revenue_this_month = round(sum(m.total_revenue for m in metrics), 2)

    stage_counts = {}
    for stage in ["draft", "review", "approved", "listed", "live"]:
        count = await db.scalar(
            select(func.count(Product.id)).where(Product.stage == stage)
        ) or 0
        stage_counts[stage] = count

    return {
        "total_products": total_products,
        "pending_reviews": pending_reviews,
        "revenue_this_month": revenue_this_month,
        "stage_counts": stage_counts,
    }


@router.get("/metrics/chart")
@limiter.limit("60/minute")
async def get_metrics_chart(request: Request, days: int = 30, db: AsyncSession = Depends(get_db), user: str = Depends(api_login_required)):
    result = await db.execute(
        select(DailyMetric).order_by(desc(DailyMetric.date)).limit(days)
    )
    metrics = list(reversed(result.scalars().all()))

    return {
        "labels": [m.date.strftime("%b %d") for m in metrics],
        "revenue": [m.total_revenue for m in metrics],
        "views": [m.total_views for m in metrics],
        "sales": [m.total_sales for m in metrics],
    }


@router.get("/queue/count")
@limiter.limit("60/minute")
async def get_queue_count(request: Request, db: AsyncSession = Depends(get_db), user: str = Depends(api_login_required)):
    count = await db.scalar(
        select(func.count(Product.id)).where(Product.stage == "review")
    ) or 0
    return {"count": count}


# ------------------------------------------------------------------ #
# Research API endpoints                                               #
# ------------------------------------------------------------------ #

@router.post("/research/trigger")
@limiter.limit("10/minute")
async def trigger_research(
    request: Request,
    niche_ids: Optional[list[int]] = Body(default=None),
    db: AsyncSession = Depends(get_db),
    user: str = Depends(api_login_required),
):
    """Manually trigger the research agent. Returns Celery task ID."""
    from app.tasks.celery_app import run_research
    input_data = {"niche_ids": niche_ids} if niche_ids else {}
    task = run_research.delay(input_data=input_data)
    return {"task_id": task.id, "status": "queued"}


@router.get("/research/results")
@limiter.limit("60/minute")
async def get_research_results(
    request: Request,
    niche_id: Optional[int] = None,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    user: str = Depends(api_login_required),
):
    """Get latest research results, optionally filtered by niche."""
    query = (
        select(ResearchResult)
        .order_by(desc(ResearchResult.created_at))
        .limit(min(limit, 100))
    )
    if niche_id:
        query = query.where(ResearchResult.niche_id == niche_id)
    results = (await db.execute(query)).scalars().all()

    return [
        {
            "id": r.id,
            "niche_id": r.niche_id,
            "total_listings_found": r.total_listings_found,
            "avg_price": r.avg_price,
            "avg_views": r.avg_views,
            "avg_favourites": r.avg_favourites,
            "opportunity_score": r.opportunity_score,
            "competition_level": r.competition_level,
            "demand_signal": r.demand_signal,
            "analysis_status": r.analysis_status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in results
    ]


@router.get("/research/niches")
@limiter.limit("60/minute")
async def get_niches(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: str = Depends(api_login_required),
):
    """Get all research niches with their enabled status."""
    niches = (await db.execute(select(ResearchNiche).order_by(ResearchNiche.name))).scalars().all()
    return [
        {
            "id": n.id,
            "name": n.name,
            "keywords": n.keywords,
            "enabled": n.enabled,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
        for n in niches
    ]


@router.post("/research/niches")
@limiter.limit("20/minute")
async def create_niche(
    request: Request,
    name: str = Body(...),
    keywords: list[str] = Body(...),
    db: AsyncSession = Depends(get_db),
    user: str = Depends(api_login_required),
):
    """Add a new research niche."""
    from datetime import datetime, timezone
    existing = await db.scalar(select(ResearchNiche).where(ResearchNiche.name == name))
    if existing:
        raise HTTPException(status_code=409, detail="Niche with that name already exists")
    now = datetime.now(timezone.utc)
    niche = ResearchNiche(name=name, keywords=keywords, enabled=True, created_at=now, updated_at=now)
    db.add(niche)
    await db.flush()
    return {"id": niche.id, "name": niche.name, "keywords": niche.keywords, "enabled": niche.enabled}


@router.put("/research/niches/{niche_id}")
@limiter.limit("20/minute")
async def update_niche(
    request: Request,
    niche_id: int,
    enabled: Optional[bool] = Body(default=None),
    keywords: Optional[list[str]] = Body(default=None),
    db: AsyncSession = Depends(get_db),
    user: str = Depends(api_login_required),
):
    """Update niche enabled status or keywords."""
    from datetime import datetime, timezone
    niche = await db.get(ResearchNiche, niche_id)
    if not niche:
        raise HTTPException(status_code=404, detail="Niche not found")
    if enabled is not None:
        niche.enabled = enabled
    if keywords is not None:
        niche.keywords = keywords
    niche.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return {"id": niche.id, "name": niche.name, "keywords": niche.keywords, "enabled": niche.enabled}


@router.get("/research/tasks/{task_id}")
@limiter.limit("60/minute")
async def get_research_task_status(
    request: Request,
    task_id: str,
    user: str = Depends(api_login_required),
):
    """Return Celery task status and payload (when complete)."""
    from app.tasks.celery_app import celery_app

    result = celery_app.AsyncResult(task_id)
    payload = {
        "task_id": task_id,
        "status": result.status,
    }

    info = result.info if isinstance(result.info, dict) else None
    if info:
        payload["meta"] = info
        payload["progress_percent"] = info.get("progress_percent")

    if result.ready():
        if result.successful():
            payload["result"] = result.result
        else:
            payload["error"] = str(result.result)

    return payload

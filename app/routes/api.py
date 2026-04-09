from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.database import get_db
from app.models.agent import AgentRun
from app.models.product import Product
from app.models.metric import DailyMetric
from app.auth import api_login_required

router = APIRouter(prefix="/api")


@router.get("/api/agents/status")
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


@router.get("/api/dashboard/stats")
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


@router.get("/api/metrics/chart")
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


@router.get("/api/queue/count")
async def get_queue_count(request: Request, db: AsyncSession = Depends(get_db), user: str = Depends(api_login_required)):
    count = await db.scalar(
        select(func.count(Product.id)).where(Product.stage == "review")
    ) or 0
    return {"count": count}

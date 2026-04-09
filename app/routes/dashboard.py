from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.database import get_db
from app.models.agent import AgentRun
from app.models.product import Product
from app.models.metric import DailyMetric
from app.auth import login_required

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
async def dashboard(request: Request, db: AsyncSession = Depends(get_db), user: str = Depends(login_required)):
    total_products = await db.scalar(select(func.count(Product.id)))
    pending_reviews = await db.scalar(
        select(func.count(Product.id)).where(Product.stage == "review")
    )

    result = await db.execute(
        select(DailyMetric).order_by(desc(DailyMetric.date)).limit(30)
    )
    metrics = result.scalars().all()

    revenue_this_month = sum(m.total_revenue for m in metrics[:30])

    result = await db.execute(
        select(AgentRun).order_by(desc(AgentRun.started_at)).limit(10)
    )
    recent_runs = result.scalars().all()

    result = await db.execute(
        select(Product).where(Product.stage == "review").order_by(desc(Product.created_at)).limit(5)
    )
    review_queue = result.scalars().all()

    stage_counts = {}
    for stage in ["draft", "review", "approved", "listed", "live"]:
        count = await db.scalar(
            select(func.count(Product.id)).where(Product.stage == stage)
        )
        stage_counts[stage] = count or 0

    chart_labels = [m.date.strftime("%b %d") for m in reversed(metrics[:14])]
    chart_revenue = [m.total_revenue for m in reversed(metrics[:14])]

    agent_types = ["research", "content", "design", "listing", "analytics"]
    agent_stats = {}
    for agent_type in agent_types:
        success = await db.scalar(
            select(func.count(AgentRun.id)).where(
                AgentRun.agent_type == agent_type, AgentRun.status == "success"
            )
        ) or 0
        failed = await db.scalar(
            select(func.count(AgentRun.id)).where(
                AgentRun.agent_type == agent_type, AgentRun.status == "failed"
            )
        ) or 0
        agent_stats[agent_type] = {"success": success, "failed": failed}

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "total_products": total_products or 0,
            "pending_reviews": pending_reviews or 0,
            "revenue_this_month": round(revenue_this_month, 2),
            "recent_runs": recent_runs,
            "review_queue": review_queue,
            "stage_counts": stage_counts,
            "chart_labels": chart_labels,
            "chart_revenue": chart_revenue,
            "agent_stats": agent_stats,
            "active_page": "dashboard",
        },
    )

from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.database import get_db
from app.models.metric import DailyMetric
from app.models.agent import AgentRun
from app.models.product import Product
from app.auth import login_required

router = APIRouter(prefix="/analytics")
templates = Jinja2Templates(directory="app/templates")


@router.get("")
async def analytics(request: Request, db: AsyncSession = Depends(get_db), user: str = Depends(login_required)):
    result = await db.execute(
        select(DailyMetric).order_by(desc(DailyMetric.date)).limit(30)
    )
    metrics = list(reversed(result.scalars().all()))

    total_revenue = sum(m.total_revenue for m in metrics)
    total_sales = sum(m.total_sales for m in metrics)
    total_views = sum(m.total_views for m in metrics)
    total_agent_costs = sum(m.agent_costs for m in metrics)

    result = await db.execute(
        select(AgentRun.agent_type, func.count(AgentRun.id).label("runs"), func.sum(AgentRun.cost).label("cost"))
        .group_by(AgentRun.agent_type)
    )
    agent_breakdown = [{"agent_type": r.agent_type, "runs": r.runs, "cost": round(r.cost or 0, 4)} for r in result.all()]

    result = await db.execute(
        select(Product.niche, func.count(Product.id).label("count"))
        .group_by(Product.niche)
        .order_by(desc("count"))
        .limit(10)
    )
    niche_breakdown = [{"niche": r.niche, "count": r.count} for r in result.all()]

    chart_labels = [m.date.strftime("%b %d") for m in metrics]
    chart_revenue = [m.total_revenue for m in metrics]
    chart_views = [m.total_views for m in metrics]

    return templates.TemplateResponse(
        "analytics.html",
        {
            "request": request,
            "metrics": metrics,
            "total_revenue": round(total_revenue, 2),
            "total_sales": total_sales,
            "total_views": total_views,
            "total_agent_costs": round(total_agent_costs, 4),
            "agent_breakdown": agent_breakdown,
            "niche_breakdown": niche_breakdown,
            "chart_labels": chart_labels,
            "chart_revenue": chart_revenue,
            "chart_views": chart_views,
            "active_page": "analytics",
        },
    )

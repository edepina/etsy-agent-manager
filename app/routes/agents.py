from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.database import get_db
from app.models.agent import AgentRun

router = APIRouter(prefix="/agents")
templates = Jinja2Templates(directory="app/templates")

AGENT_DEFINITIONS = [
    {
        "type": "research",
        "name": "Research Agent",
        "description": "Discovers trending Islamic digital product opportunities on Etsy",
        "icon": "search",
        "schedule": "Every Monday 6:00 AM",
        "celery_task": "app.tasks.celery_app.run_research",
    },
    {
        "type": "content",
        "name": "Content Agent",
        "description": "Generates SEO-optimised titles, descriptions, and tags via Claude",
        "icon": "edit_note",
        "schedule": "On demand",
        "celery_task": "app.tasks.celery_app.run_content",
    },
    {
        "type": "design",
        "name": "Design Agent",
        "description": "Creates PDF and image files for digital products",
        "icon": "design_services",
        "schedule": "On demand",
        "celery_task": "app.tasks.celery_app.run_design",
    },
    {
        "type": "listing",
        "name": "Listing Agent",
        "description": "Publishes approved products to Etsy as active listings",
        "icon": "storefront",
        "schedule": "On approval",
        "celery_task": "app.tasks.celery_app.run_listing",
    },
    {
        "type": "analytics",
        "name": "Analytics Agent",
        "description": "Pulls shop stats and updates performance metrics daily",
        "icon": "bar_chart",
        "schedule": "Daily 7:00 AM",
        "celery_task": "app.tasks.celery_app.run_analytics",
    },
]


@router.get("")
async def agents_overview(request: Request, db: AsyncSession = Depends(get_db)):
    agents_with_stats = []
    for agent_def in AGENT_DEFINITIONS:
        last_run = await db.execute(
            select(AgentRun)
            .where(AgentRun.agent_type == agent_def["type"])
            .order_by(desc(AgentRun.started_at))
            .limit(1)
        )
        last_run = last_run.scalars().first()

        success_count = await db.scalar(
            select(func.count(AgentRun.id)).where(
                AgentRun.agent_type == agent_def["type"], AgentRun.status == "success"
            )
        ) or 0
        fail_count = await db.scalar(
            select(func.count(AgentRun.id)).where(
                AgentRun.agent_type == agent_def["type"], AgentRun.status == "failed"
            )
        ) or 0

        agents_with_stats.append({
            **agent_def,
            "last_run": last_run,
            "success_count": success_count,
            "fail_count": fail_count,
            "status": last_run.status if last_run else "idle",
        })

    return templates.TemplateResponse(
        "agents.html",
        {
            "request": request,
            "agents": agents_with_stats,
            "active_page": "agents",
        },
    )


@router.get("/{agent_type}")
async def agent_detail(agent_type: str, request: Request, db: AsyncSession = Depends(get_db)):
    agent_def = next((a for a in AGENT_DEFINITIONS if a["type"] == agent_type), None)
    if not agent_def:
        raise HTTPException(status_code=404, detail="Agent not found")

    result = await db.execute(
        select(AgentRun)
        .where(AgentRun.agent_type == agent_type)
        .order_by(desc(AgentRun.started_at))
        .limit(50)
    )
    runs = result.scalars().all()

    success_count = sum(1 for r in runs if r.status == "success")
    fail_count = sum(1 for r in runs if r.status == "failed")
    total_cost = sum(r.cost or 0 for r in runs)
    total_tokens = sum(r.tokens_used or 0 for r in runs)

    return templates.TemplateResponse(
        "agent_detail.html",
        {
            "request": request,
            "agent": agent_def,
            "runs": runs,
            "success_count": success_count,
            "fail_count": fail_count,
            "total_cost": round(total_cost, 4),
            "total_tokens": total_tokens,
            "active_page": "agents",
        },
    )


@router.post("/{agent_type}/trigger")
async def trigger_agent(agent_type: str, db: AsyncSession = Depends(get_db)):
    agent_def = next((a for a in AGENT_DEFINITIONS if a["type"] == agent_type), None)
    if not agent_def:
        raise HTTPException(status_code=404, detail="Agent not found")

    from app.tasks.celery_app import (
        run_research, run_content, run_design, run_listing, run_analytics
    )

    task_map = {
        "research": run_research,
        "content": run_content,
        "design": run_design,
        "listing": run_listing,
        "analytics": run_analytics,
    }

    task_fn = task_map.get(agent_type)
    if task_fn:
        task_fn.delay(input_data={})

    return RedirectResponse(url=f"/agents/{agent_type}", status_code=303)

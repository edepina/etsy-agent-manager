from fastapi import APIRouter, Request, Depends, HTTPException, Query
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db
from app.models.product import Product
from app.auth import login_required, generate_csrf_token

router = APIRouter(prefix="/products")
templates = Jinja2Templates(directory="app/templates")


@router.get("")
async def products_pipeline(
    request: Request,
    stage: str = None,
    niche: str = None,
    db: AsyncSession = Depends(get_db),
    user: str = Depends(login_required),
):
    query = select(Product).order_by(desc(Product.created_at))

    if stage:
        query = query.where(Product.stage == stage)
    if niche:
        query = query.where(Product.niche.ilike(f"%{niche}%"))

    result = await db.execute(query)
    products = result.scalars().all()

    stage_groups = {}
    for s in ["draft", "review", "approved", "listed", "live"]:
        stage_groups[s] = [p for p in products if p.stage == s]

    niches = list({p.niche for p in products})

    return templates.TemplateResponse(
        "products.html",
        {
            "request": request,
            "products": products,
            "stage_groups": stage_groups,
            "niches": niches,
            "selected_stage": stage,
            "selected_niche": niche,
            "active_page": "products",
            "csrf_token": generate_csrf_token(request),
        },
    )


@router.get("/{product_id}")
async def product_detail(product_id: int, request: Request, db: AsyncSession = Depends(get_db), user: str = Depends(login_required)):
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return templates.TemplateResponse(
        "products.html",
        {
            "request": request,
            "product": product,
            "detail_view": True,
            "active_page": "products",
        },
    )

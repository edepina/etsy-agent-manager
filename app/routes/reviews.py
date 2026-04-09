from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, update

from app.database import get_db
from app.models.product import Product
from app.auth import login_required, generate_csrf_token, validate_csrf_token

router = APIRouter(prefix="/reviews")
templates = Jinja2Templates(directory="app/templates")


@router.get("")
async def review_queue(request: Request, db: AsyncSession = Depends(get_db), user: str = Depends(login_required)):
    result = await db.execute(
        select(Product).where(Product.stage == "review").order_by(desc(Product.created_at))
    )
    items = result.scalars().all()

    return templates.TemplateResponse(
        "reviews.html",
        {
            "request": request,
            "items": items,
            "count": len(items),
            "active_page": "reviews",
            "csrf_token": generate_csrf_token(request),
        },
    )


@router.post("/{product_id}/approve")
async def approve_product(
    request: Request,
    product_id: int,
    csrf_token: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user: str = Depends(login_required),
):
    if not validate_csrf_token(request, csrf_token):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    await db.execute(
        update(Product).where(Product.id == product_id).values(stage="approved")
    )
    await db.commit()
    return RedirectResponse(url="/reviews", status_code=303)


@router.post("/{product_id}/reject")
async def reject_product(
    request: Request,
    product_id: int,
    csrf_token: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user: str = Depends(login_required),
):
    if not validate_csrf_token(request, csrf_token):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    await db.execute(
        update(Product).where(Product.id == product_id).values(stage="draft")
    )
    await db.commit()
    return RedirectResponse(url="/reviews", status_code=303)

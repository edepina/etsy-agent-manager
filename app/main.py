from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine, Base
from app.routes import dashboard, agents, products, reviews, analytics, api


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="Etsy Agent Manager",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(dashboard.router)
app.include_router(agents.router)
app.include_router(products.router)
app.include_router(reviews.router)
app.include_router(analytics.router)
app.include_router(api.router)

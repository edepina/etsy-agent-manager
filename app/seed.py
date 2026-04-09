"""
Seed the database with mock data so the dashboard looks populated on first run.
Run with: python -m app.seed
"""
import asyncio
import random
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.config import settings
from app.models.agent import AgentRun
from app.models.product import Product
from app.models.workflow import Workflow
from app.models.metric import DailyMetric

NICHES = [
    "Ramadan Planner", "Islamic Wall Art", "Eid Invitation", "Quran Journal",
    "Prayer Tracker", "Hijri Calendar", "Dua Checklist", "Islamic Kids Activity",
    "Nikah Invitation", "Hajj Planner",
]
PRODUCT_TYPES = ["planner", "printable", "wall_art", "journal", "checklist", "invitation"]
STAGES = ["draft", "review", "approved", "listed", "live"]
AGENT_TYPES = ["research", "content", "design", "listing", "analytics"]

SAMPLE_TITLES = [
    "30-Day Ramadan Planner | Islamic Printable | Digital Download",
    "Bismillah Wall Art | Islamic Home Decor | Printable PDF",
    "Eid Mubarak Invitation Template | Editable | Instant Download",
    "Quran Reflection Journal | Daily Dhikr | Islamic Planner",
    "5 Daily Prayers Tracker | Salah Habit | Printable Checklist",
    "Hijri Calendar 2025 | Islamic Wall Calendar | Printable",
    "Morning & Evening Duas | Islamic Checklist | Digital Download",
    "Islamic Kids Activity Book | Quran Learning | Printable",
    "Nikah Invitation | Islamic Wedding Card | Editable Template",
    "Hajj & Umrah Planner | Step-by-Step Guide | Printable PDF",
    "Ramadan Meal Planner | Suhoor & Iftar | Islamic Printable",
    "99 Names of Allah Poster | Wall Art | Printable PDF",
    "Islamic Vision Board | Muslim Goal Setting | Planner",
    "Eid Al-Adha Party Invitation | Printable Template",
    "Quran Memorisation Tracker | Hifz Journal | Printable",
    "Islamic Gratitude Journal | Alhamdulillah Daily | Printable",
    "Zakat Calculator & Tracker | Islamic Finance | Printable",
    "Kids Islamic Colouring Pages | Arabic Letters | Printable",
    "Muslim Wedding Checklist | Nikah Preparation | Printable",
    "Sadaqah Jar Labels & Tracker | Islamic Charity | Printable",
]


async def seed(db: AsyncSession) -> None:
    print("Seeding products...")
    products = []
    for i, title in enumerate(SAMPLE_TITLES):
        niche = NICHES[i % len(NICHES)]
        p_type = PRODUCT_TYPES[i % len(PRODUCT_TYPES)]
        stage = STAGES[i % len(STAGES)]
        created = datetime.now(timezone.utc) - timedelta(days=random.randint(0, 60))
        product = Product(
            name=title,
            type=p_type,
            niche=niche,
            stage=stage,
            file_path=f"products/{niche.lower().replace(' ', '-')}-{i+1}.pdf" if stage not in ("draft",) else None,
            description=f"Beautifully designed {niche} printable for Muslim households. Instant download PDF.",
            etsy_listing_id=f"1{random.randint(100000000, 999999999)}" if stage in ("listed", "live") else None,
            created_at=created,
            updated_at=created,
        )
        db.add(product)
        products.append(product)

    await db.flush()

    print("Seeding agent runs...")
    statuses = ["success", "success", "success", "failed"]
    for i in range(50):
        agent_type = AGENT_TYPES[i % len(AGENT_TYPES)]
        status = random.choice(statuses)
        started = datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 720))
        completed = started + timedelta(seconds=random.randint(2, 60))
        run = AgentRun(
            agent_type=agent_type,
            status=status,
            input_data={"niche": random.choice(NICHES)},
            output_data={"result": "mock"} if status == "success" else None,
            error="Mock connection error" if status == "failed" else None,
            tokens_used=random.randint(0, 2000) if agent_type == "content" else 0,
            cost=round(random.uniform(0, 0.05), 6) if agent_type == "content" else 0.0,
            started_at=started,
            completed_at=completed,
        )
        db.add(run)

    print("Seeding daily metrics...")
    for i in range(30):
        day = date.today() - timedelta(days=29 - i)
        metric = DailyMetric(
            date=day,
            total_products=len(products) - random.randint(0, 5),
            total_sales=random.randint(0, 15),
            total_revenue=round(random.uniform(0, 75), 2),
            total_views=random.randint(20, 400),
            agent_runs=random.randint(0, 10),
            agent_costs=round(random.uniform(0, 0.25), 6),
        )
        db.add(metric)

    print("Seeding workflows...")
    full_pipeline = Workflow(
        name="Full Pipeline",
        steps=["research", "content", "design", "review", "listing"],
        schedule="0 6 * * 1",
        enabled=True,
    )
    analytics_workflow = Workflow(
        name="Daily Analytics",
        steps=["analytics"],
        schedule="0 7 * * *",
        enabled=True,
    )
    db.add(full_pipeline)
    db.add(analytics_workflow)

    await db.commit()
    print("Seed complete!")


async def main():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        from app.database import Base
        import app.models  # noqa
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as session:
        await seed(session)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

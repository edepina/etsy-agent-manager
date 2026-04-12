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
from app.models.research import ResearchNiche

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


ALL_NICHES = [
    # --- Existing niches: merged keywords + updated enabled flags ---
    {
        "name": "Ramadan Planners",
        "keywords": [
            "ramadan planner", "ramadan printable", "ramadan journal", "ramadan tracker",
            "ramadan calendar", "ramadan planner beginners", "ramadan planner busy moms",
            "ramadan planner students", "ramadan planner new revert", "ramadan business planner",
            "ramadan content calendar", "ramadan charity planner",
        ],
        "enabled": False,  # Ramadan just passed — re-enable ~8 weeks before next Ramadan
    },
    {
        "name": "Islamic Wall Art",
        "keywords": [
            "islamic wall art", "islamic print", "bismillah art", "allah wall art",
            "arabic calligraphy print", "islamic nursery art", "minimalist arabic calligraphy",
            "islamic calligraphy set", "three piece islamic wall art", "modern islamic print",
        ],
        "enabled": True,
    },
    {
        "name": "Qur'an Journals",
        "keywords": [
            "quran journal", "quran study guide", "quran reflection journal",
            "quran tracker", "islamic journal",
        ],
        "enabled": True,
    },
    {
        "name": "Du'a Collections",
        "keywords": [
            "dua printable", "dua cards", "dua book", "islamic prayer cards", "daily dua",
            "morning dua", "daily dua journal", "answered dua log", "shukr gratitude journal",
            "islamic gratitude prompts",
        ],
        "enabled": True,
    },
    {
        "name": "Islamic Wedding",
        "keywords": [
            "islamic wedding invitation", "nikah invitation", "walimah invitation",
            "muslim wedding", "nikkah printable", "nikah planning kit", "mahr planner",
            "walimah seating chart", "muslim wedding vendor tracker", "islamic wedding guest list",
        ],
        "enabled": True,
    },
    {
        "name": "Hajj & Umrah",
        "keywords": [
            "hajj planner", "umrah checklist", "hajj printable", "hajj journal",
            "umrah planner", "hajj packing list", "umrah trip planner", "hajj ritual checklist",
            "hajj budget sheet", "hajj dua list", "umrah packing list printable",
            "hajj step by step guide",
        ],
        "enabled": True,  # Hajj season approaching
    },
    {
        "name": "Islamic Education",
        "keywords": [
            "islamic homeschool", "islamic worksheet", "arabic alphabet printable",
            "islamic colouring", "islamic activity", "ramadan activity kids",
            "islamic lesson plan", "weekend madrasah plan", "islamic homeschool printable",
            "islamic studies worksheet",
        ],
        "enabled": True,
    },
    {
        "name": "Eid Printables",
        "keywords": [
            "eid decoration", "eid printable", "eid banner", "eid card printable",
            "eid party", "eid mubarak printable", "eid al adha printable",
            "eid party games", "eid thank you card", "eid money envelope printable",
        ],
        "enabled": False,  # Eid just passed — re-enable before next Eid
    },

    # --- New niches: ENABLED (high priority) ---
    {
        "name": "Tajweed Practice Sheets",
        "keywords": [
            "tajweed worksheet", "tajweed rules printable", "tajweed practice sheet",
            "quran recitation tracker", "tajweed colour coded", "tajweed mistakes log",
        ],
        "enabled": True,
    },
    {
        "name": "Daily Muslim Productivity",
        "keywords": [
            "muslim productivity planner", "daily muslim planner", "salah habit tracker",
            "adhkar tracker printable", "islamic daily routine", "muslim goal planner",
            "islamic habit tracker",
        ],
        "enabled": True,
    },
    {
        "name": "New Revert Roadmap",
        "keywords": [
            "new muslim guide", "revert islam planner", "new shahada planner",
            "convert islam checklist", "new muslim learning plan", "islam basics printable",
            "new revert salah guide",
        ],
        "enabled": True,
    },
    {
        "name": "Salah & Wudu Charts for Kids",
        "keywords": [
            "salah chart kids", "wudu steps printable", "how to pray poster kids",
            "salah reward chart", "wudu chart children", "islamic prayer steps kids",
        ],
        "enabled": True,
    },
    {
        "name": "Arabic Alphabet Workbooks",
        "keywords": [
            "arabic alphabet tracing", "arabic letter worksheet", "arabic flashcards printable",
            "learn arabic alphabet kids", "arabic writing practice", "arabic alphabet poster",
        ],
        "enabled": True,
    },
    {
        "name": "Aqiqah & Baby Naming",
        "keywords": [
            "aqiqah planner", "aqiqah invitation printable", "islamic baby naming",
            "aqiqah checklist", "islamic nursery print", "bismillah baby shower",
            "muslim baby shower printable",
        ],
        "enabled": True,
    },
    {
        "name": "Minimalist Arabic Calligraphy Sets",
        "keywords": [
            "arabic calligraphy bundle", "bismillah calligraphy print",
            "subhanallah alhamdulillah print set", "islamic typography art",
            "modern arabic art print", "islamic calligraphy trio",
        ],
        "enabled": True,
    },
    {
        "name": "Kids Islamic Affirmation Prints",
        "keywords": [
            "islamic kids poster", "muslim affirmation print", "islamic bedroom art kids",
            "i am kind islamic print", "islamic values poster children",
            "muslim kids room decor",
        ],
        "enabled": True,
    },
    {
        "name": "Dhul Hijjah & Arafah Planners",
        "keywords": [
            "dhul hijjah planner", "day of arafah planner", "dhul hijjah ibadah tracker",
            "10 days dhul hijjah", "dhul hijjah fasting tracker", "takbeer printable",
            "dhul hijjah dua list",
        ],
        "enabled": True,  # Dhul Hijjah approaching
    },
    {
        "name": "Halal Budgeting & Finance",
        "keywords": [
            "halal budget planner", "islamic finance printable", "zakat calculator printable",
            "riba free budget", "sadaqah tracker", "muslim savings planner",
            "halal debt free planner",
        ],
        "enabled": True,
    },

    # --- New niches: DISABLED (medium priority, enable after research validates demand) ---
    {
        "name": "Islamic Parenting Journals",
        "keywords": [
            "islamic parenting planner", "tarbiyah journal", "muslim parenting reflection",
            "raising muslim children planner", "islamic character building worksheet",
            "muslim mom planner",
        ],
        "enabled": False,
    },
    {
        "name": "Istikhara & Decision Journals",
        "keywords": [
            "istikhara journal", "islamic decision journal", "istikhara dua printable",
            "muslim life choices planner", "tawakkul journal", "islamic reflection prompts",
        ],
        "enabled": False,
    },
    {
        "name": "Qur'an Memorisation Trackers for Kids",
        "keywords": [
            "hifz tracker kids", "juz amma chart", "quran memorization chart children",
            "surah tracker printable kids", "hifz reward chart", "quran progress kids",
        ],
        "enabled": False,
    },
    {
        "name": "Adult Hifz & Revision Planners",
        "keywords": [
            "hifz planner adult", "quran revision calendar", "spaced repetition quran",
            "surah revision log", "hifz journal", "quran memorization planner adult",
        ],
        "enabled": False,
    },
    {
        "name": "Qur'anic Vocabulary Flashcards",
        "keywords": [
            "quranic arabic flashcards", "quran vocabulary cards", "arabic quran words",
            "islamic vocabulary printable", "quran word meanings cards",
        ],
        "enabled": False,
    },
    {
        "name": "Tawakkul & Sabr Workbooks",
        "keywords": [
            "islamic mindset journal", "sabr journal", "tawakkul workbook",
            "islamic mental health printable", "muslim wellbeing journal",
            "islamic self care planner",
        ],
        "enabled": False,
    },
    {
        "name": "Canva Social Media Packs for Muslim Brands",
        "keywords": [
            "islamic social media templates", "muslim brand canva templates",
            "jummah reminder template", "islamic instagram post template",
            "ramadan social media kit", "eid announcement template",
        ],
        "enabled": False,
    },
    {
        "name": "Islamic Event Invitation Templates",
        "keywords": [
            "islamic invitation template", "quran khatam invitation",
            "islamic party invitation", "ameen ceremony invitation",
            "islamic housewarming invitation", "walimah invitation template",
        ],
        "enabled": False,
    },
    {
        "name": "Halal Small Business Finance",
        "keywords": [
            "halal business planner", "islamic profit sharing calculator",
            "halal product costing sheet", "muslim entrepreneur planner",
            "islamic business finance template",
        ],
        "enabled": False,
    },
    {
        "name": "Masjid Themed Nursery Art",
        "keywords": [
            "masjid nursery print", "cute mosque art kids", "islamic nursery decor",
            "moon star nursery print", "muslim baby room art", "masjid illustration print",
        ],
        "enabled": False,
    },
    {
        "name": "Islamic Motivational Quotes",
        "keywords": [
            "islamic quote printable", "muslim motivational poster",
            "islamic office wall art", "quran quote print", "hadith quote poster",
            "islamic study room decor",
        ],
        "enabled": False,
    },
    {
        "name": "Dervish & Tasawwuf Art",
        "keywords": [
            "whirling dervish art", "sufi art print", "dervish silhouette",
            "tasawwuf wall art", "dhikr art print", "islamic spiritual art",
        ],
        "enabled": False,
    },
    {
        "name": "Islamic Funeral & Janazah Checklists",
        "keywords": [
            "janazah checklist", "islamic funeral planner", "islamic burial checklist",
            "janazah dua printable", "muslim funeral preparation", "ghusl checklist",
        ],
        "enabled": False,
    },

    # --- New niches: DISABLED (seasonal — enable when season approaches) ---
    {
        "name": "Kids Ramadan Activity Books",
        "keywords": [
            "ramadan activity book kids", "ramadan coloring pages", "ramadan maze kids",
            "ramadan good deed chart", "ramadan daily hadith kids",
            "ramadan printable activities children",
        ],
        "enabled": False,  # Enable ~6 weeks before Ramadan
    },
    {
        "name": "Last 10 Nights Qadr Planner",
        "keywords": [
            "laylatul qadr planner", "last 10 nights ramadan", "last ten nights ibadah",
            "qadr night dua list", "ramadan last 10 nights schedule",
            "laylatul qadr worship planner",
        ],
        "enabled": False,  # Enable ~4 weeks before Ramadan
    },
    {
        "name": "Ramadan Business Owners Planner",
        "keywords": [
            "ramadan business planner", "ramadan marketing calendar",
            "iftar event planner", "ramadan campaign planner",
            "islamic business ramadan", "ramadan charity campaign planner",
        ],
        "enabled": False,  # Enable ~8 weeks before Ramadan
    },
]


async def seed(db: AsyncSession) -> None:
    from sqlalchemy import select, func
    print("Seeding research niches (idempotent upsert)...")
    added = updated = skipped = 0
    for niche_data in ALL_NICHES:
        existing = await db.scalar(
            select(ResearchNiche).where(
                func.lower(ResearchNiche.name) == niche_data["name"].lower()
            )
        )
        if existing:
            current_kws = set(existing.keywords or [])
            new_kws = set(niche_data["keywords"])
            merged = sorted(current_kws | new_kws)
            changed = False
            if merged != sorted(current_kws):
                existing.keywords = merged
                changed = True
            if existing.enabled != niche_data["enabled"]:
                existing.enabled = niche_data["enabled"]
                changed = True
            if changed:
                existing.updated_at = datetime.now(timezone.utc)
                updated += 1
                print(f"  UPDATED: {existing.name}")
            else:
                skipped += 1
        else:
            db.add(ResearchNiche(
                name=niche_data["name"],
                keywords=niche_data["keywords"],
                enabled=niche_data["enabled"],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            ))
            added += 1
            print(f"  ADDED:   {niche_data['name']}")
    await db.flush()
    await db.commit()
    print(f"Niches: {added} added, {updated} updated, {skipped} unchanged.")

    from sqlalchemy import select as _select
    existing_products = await db.scalar(_select(func.count()).select_from(Product))
    if existing_products > 0:
        print("Mock data already seeded — skipping products, agent runs, metrics, workflows.")
        return

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
    print("Seed complete.")


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

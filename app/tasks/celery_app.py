from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery(
    "etsy_agent_manager",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.celery_app"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

celery_app.conf.beat_schedule = {
    "run-research-weekly": {
        "task": "app.tasks.celery_app.run_research",
        "schedule": crontab(hour=6, minute=0, day_of_week="monday"),
        "kwargs": {"input_data": {}},
    },
    "run-analytics-daily": {
        "task": "app.tasks.celery_app.run_analytics",
        "schedule": crontab(hour=7, minute=0),
        "kwargs": {"input_data": {}},
    },
}


def _run_agent_sync(agent_class_name: str, input_data: dict, progress_callback=None) -> dict:
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from app.config import settings as _settings
    import importlib

    agents_module = importlib.import_module("app.agents")
    AgentClass = getattr(agents_module, agent_class_name)
    agent = AgentClass()

    if progress_callback and hasattr(agent, "set_progress_callback"):
        agent.set_progress_callback(progress_callback)

    engine = create_async_engine(_settings.DATABASE_URL, echo=False)
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def _run():
        async with SessionLocal() as session:
            result = await agent.execute(input_data, session)
            await session.commit()
            return result

    return asyncio.run(_run())


@celery_app.task(bind=True, max_retries=3, name="app.tasks.celery_app.run_research")
def run_research(self, input_data: dict = None):
    try:
        def _progress(meta: dict):
            self.update_state(state="PROGRESS", meta=meta)

        return _run_agent_sync("ResearchAgent", input_data or {}, progress_callback=_progress)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3, name="app.tasks.celery_app.run_content")
def run_content(self, input_data: dict = None):
    try:
        return _run_agent_sync("ContentAgent", input_data or {})
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3, name="app.tasks.celery_app.run_design")
def run_design(self, input_data: dict = None):
    try:
        return _run_agent_sync("DesignAgent", input_data or {})
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3, name="app.tasks.celery_app.run_listing")
def run_listing(self, input_data: dict = None):
    try:
        return _run_agent_sync("ListingAgent", input_data or {})
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3, name="app.tasks.celery_app.run_analytics")
def run_analytics(self, input_data: dict = None):
    try:
        return _run_agent_sync("AnalyticsAgent", input_data or {})
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=2, name="app.tasks.celery_app.run_full_pipeline")
def run_full_pipeline(self, input_data: dict = None):
    try:
        return _run_agent_sync("MasterController", input_data or {})
    except Exception as exc:
        raise self.retry(exc=exc, countdown=120)

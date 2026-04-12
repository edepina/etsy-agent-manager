import asyncio
import time
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Callable, Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import AgentRun

logger = logging.getLogger(__name__)


class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PAUSED = "paused"


class BaseAgent:
    """All agents inherit from this. Provides:
    - run(input_data: dict) -> dict — main execution method
    - log_run() — saves run to database with status, duration, tokens, cost
    - get_status() -> AgentStatus — current state
    - retry(max_retries=3) — retry logic with exponential backoff
    """

    agent_type: str = "base"

    def __init__(self):
        self._status = AgentStatus.IDLE
        self._last_run: Optional[datetime] = None
        self._last_error: Optional[str] = None
        self._progress_callback: Optional[Callable[[dict[str, Any]], None]] = None

    def set_progress_callback(self, callback: Callable[[dict[str, Any]], None]) -> None:
        self._progress_callback = callback

    def report_progress(self, payload: dict[str, Any]) -> None:
        if self._progress_callback:
            self._progress_callback(payload)

    async def run(self, input_data: dict, db: AsyncSession) -> dict:
        raise NotImplementedError("Subclasses must implement run()")

    async def execute(self, input_data: dict, db: AsyncSession) -> dict:
        self._status = AgentStatus.RUNNING
        start_time = time.time()
        run = AgentRun(
            agent_type=self.agent_type,
            status="running",
            input_data=input_data,
        )
        db.add(run)
        await db.flush()

        try:
            result = await self.run(input_data, db)
            elapsed = time.time() - start_time
            run.status = "success"
            run.output_data = result
            run.completed_at = datetime.now(timezone.utc)
            run.tokens_used = result.get("tokens_used", 0)
            run.cost = result.get("cost", 0.0)
            self._status = AgentStatus.SUCCESS
            self._last_run = datetime.now(timezone.utc)
            logger.info(f"{self.agent_type} completed in {elapsed:.2f}s")
            return result
        except Exception as e:
            run.status = "failed"
            run.error = str(e)
            run.completed_at = datetime.now(timezone.utc)
            self._status = AgentStatus.FAILED
            self._last_error = str(e)
            logger.error(f"{self.agent_type} failed: {e}")
            raise
        finally:
            await db.flush()

    async def execute_with_retry(self, input_data: dict, db: AsyncSession, max_retries: int = 3) -> dict:
        for attempt in range(max_retries):
            try:
                return await self.execute(input_data, db)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                wait = 2 ** attempt
                logger.warning(f"{self.agent_type} attempt {attempt + 1} failed, retrying in {wait}s: {e}")
                await asyncio.sleep(wait)

    def get_status(self) -> AgentStatus:
        return self._status

    def get_last_run(self) -> Optional[datetime]:
        return self._last_run

    def get_last_error(self) -> Optional[str]:
        return self._last_error

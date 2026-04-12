"""Research agent database models."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, Float, ForeignKey, Integer, JSON, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ResearchNiche(Base):
    """A niche category that the research agent tracks."""

    __tablename__ = "research_niches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    keywords: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    results: Mapped[list["ResearchResult"]] = relationship(
        "ResearchResult", back_populates="niche", cascade="all, delete-orphan"
    )


class ResearchResult(Base):
    """Results from a research agent run for a specific niche."""

    __tablename__ = "research_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    agent_run_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("agent_runs.id"), nullable=True
    )
    niche_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("research_niches.id"), nullable=False, index=True
    )

    # Raw data from Etsy
    total_listings_found: Mapped[int] = mapped_column(Integer, default=0)
    avg_price: Mapped[float] = mapped_column(Float, default=0.0)
    min_price: Mapped[float] = mapped_column(Float, default=0.0)
    max_price: Mapped[float] = mapped_column(Float, default=0.0)
    avg_views: Mapped[int] = mapped_column(Integer, default=0)
    avg_favourites: Mapped[int] = mapped_column(Integer, default=0)
    top_tags: Mapped[list] = mapped_column(JSON, default=list)
    sample_listings: Mapped[list] = mapped_column(JSON, default=list)

    # AI analysis from Claude
    opportunity_score: Mapped[int] = mapped_column(Integer, default=0)
    competition_level: Mapped[str] = mapped_column(String(20), default="unknown")
    demand_signal: Mapped[str] = mapped_column(String(20), default="unknown")
    analysis_summary: Mapped[str] = mapped_column(Text, default="")
    suggested_products: Mapped[list] = mapped_column(JSON, default=list)
    gaps_identified: Mapped[list] = mapped_column(JSON, default=list)

    # Status for retry if Claude failed
    analysis_status: Mapped[str] = mapped_column(
        String(30), default="complete"
    )  # complete | pending_analysis | error

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    niche: Mapped["ResearchNiche"] = relationship("ResearchNiche", back_populates="results")
    agent_run: Mapped[Optional["AgentRun"]] = relationship("AgentRun")  # type: ignore[name-defined]

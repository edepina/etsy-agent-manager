# Windsurf Prompt: Phase 1 — Research Agent

## Mandatory Rules (apply to ALL work in this project)

### 1. Maxton Template Adherence
This project uses the **Maxton Bootstrap 5 Admin Dashboard Template** (purchased). All UI work MUST use the actual Maxton template components, classes, and layout patterns. Specifically:
- All pages extend `base.html` which loads Maxton's CSS/JS
- Use Maxton's card components, table components (DataTables), badge classes, chart integrations (ApexCharts), form components, and alert styles exactly as they appear in the template
- Reference the existing Maxton pages in `static/assets/` for the correct HTML structure — do NOT invent custom CSS or components when a Maxton equivalent exists
- Sidebar, topbar, page wrapper structure must match the existing pages
- When in doubt, look at how `dashboard.html`, `products.html`, or `agents.html` are structured and follow the same patterns

### 2. Documentation & Git
After completing all implementation work:
- Update `PROJECT.md` — mark completed tasks with ✅, add notes where relevant, update the Changelog table with today's date and a summary of what was done
- Git commit with a clear message: `git add . && git commit -m "Phase 1: Research Agent — [summary]" && git push`
- If any new decisions were made (e.g. model design choices, API patterns), add them to the Notes & Decisions Log in PROJECT.md

### 3. Agent Skills (follow these workflows)

Before writing any code, read and follow the processes defined in these skill files:
- `.agent-skills/skills/incremental-implementation/SKILL.md` — Build in thin vertical slices, verify each before expanding
- `.agent-skills/skills/api-and-interface-design/SKILL.md` — Clean interface design for the Etsy API integration and agent interfaces
- `.agent-skills/skills/test-driven-development/SKILL.md` — Write tests before or alongside code, never ship without verification
- `.agent-skills/skills/security-and-hardening/SKILL.md` — API key handling, input validation, rate limiting awareness

---

## Context

This is the **Etsy Agent Manager** project — a FastAPI + Jinja2 + Maxton Bootstrap 5 dashboard that orchestrates AI agents to research, create, and list Islamic digital products on Etsy.

**What's already built (Phase 0):**
- Full project structure with FastAPI, Docker Compose (app, worker, beat, db, redis, caddy)
- Maxton-styled dashboard with mock data, all templates extending base.html
- Authentication (session-based login, brute-force protection, CSRF)
- HTTPS via Caddy at https://etsy.cciesolutions.net
- Database models: Agent, Product, Workflow, EtsyListing, DailyMetric
- Agent base classes in `app/agents/base.py`
- Celery + Redis task queue with Beat scheduler
- Seed script with mock data

**Etsy API credentials are in `.env`:**
```
ETSY_API_KEY=<configured>
ETSY_SHARED_SECRET=<configured>
```

**Rate limits:** 5 QPS, 5,000 queries per day.

---

## Goal

Build a fully functional Research Agent that:
1. Searches Etsy for Islamic digital products across multiple niches
2. Collects listing data (title, price, views, favourites, sales estimates, tags)
3. Sends the collected data to Claude for analysis and opportunity scoring
4. Stores research results in the database
5. Displays results in the dashboard with actionable insights
6. Runs on a weekly schedule via Celery Beat, with manual trigger option

---

## Implementation Plan (follow incremental-implementation skill)

Build this in 5 slices. Each slice must work independently and be tested before moving to the next.

### Slice 1: Etsy API Service

**File:** `app/services/etsy.py`

Build the EtsyService class that wraps the Etsy Open API v3. This is a pure HTTP client — no agent logic, no Claude, no database.

**Etsy API Details:**
- Base URL: `https://openapi.etsy.com/v3/application`
- Authentication: `x-api-key` header with your API keystring
- Key endpoint: `GET /listings/active` (findAllListingsActive)
- Parameters: `keywords` (search terms), `limit` (max 100), `offset` (max 12000), `sort_on` (created, price, updated, score), `sort_order` (asc, desc), `min_price`, `max_price`, `taxonomy_id`
- Response includes: `listing_id`, `title`, `description`, `price`, `currency_code`, `quantity`, `tags` (array), `views`, `num_favorers`, `url`, `shop_id`, `taxonomy_id`, `creation_tsz`, `last_modified_tsz`
- Pagination: default 25 per page, max 100. Use `limit` and `offset`. Response includes `count` for total results.
- Rate limit: 5 QPS, 5K per day — implement a simple delay between requests (0.25s minimum between calls)

**Methods to implement:**
```python
class EtsyService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openapi.etsy.com/v3/application"
        self.client = httpx.AsyncClient(...)

    async def search_listings(
        self,
        keywords: str,
        limit: int = 100,
        offset: int = 0,
        sort_on: str = "score",
        sort_order: str = "desc",
        min_price: float | None = None,
        max_price: float | None = None,
    ) -> dict:
        """Search active listings. Returns raw API response."""

    async def get_listing(self, listing_id: int) -> dict:
        """Get a single listing by ID."""

    async def get_shop(self, shop_id: int) -> dict:
        """Get shop details."""

    async def get_listing_images(self, listing_id: int) -> list[dict]:
        """Get images for a listing."""

    async def get_reviews_by_listing(self, listing_id: int, limit: int = 25) -> dict:
        """Get reviews for a listing."""

    async def search_niche(self, niche_keywords: list[str], max_results: int = 200) -> list[dict]:
        """
        High-level method: searches multiple keyword variations for a niche,
        deduplicates results by listing_id, returns combined list.
        Respects rate limits with delays between calls.
        """
```

**Important:**
- Use `httpx.AsyncClient` with a timeout of 30 seconds
- Include proper error handling — Etsy returns 429 for rate limits, 403 for auth issues, 404 for not found
- On 429 responses, wait and retry (up to 3 retries with exponential backoff)
- Log all API calls with response status codes
- Never expose API keys in logs or error messages

**Test:** Write tests using `pytest` and `respx` (httpx mock library) or `unittest.mock` to mock Etsy API responses. Test: successful search, empty results, rate limit handling, auth error handling, network timeout.

---

### Slice 2: Research Database Model

**File:** `app/models/research.py`

Create the ResearchResult and ResearchNiche models to store research data.

```python
class ResearchNiche(Base):
    """A niche category that the research agent tracks."""
    __tablename__ = "research_niches"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]                           # e.g. "Ramadan Planners"
    keywords: Mapped[list] = mapped_column(JSON) # ["ramadan planner", "ramadan printable", ...]
    enabled: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]

    results = relationship("ResearchResult", back_populates="niche")


class ResearchResult(Base):
    """Results from a research agent run for a specific niche."""
    __tablename__ = "research_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    agent_run_id: Mapped[int] = mapped_column(ForeignKey("agent_runs.id"))
    niche_id: Mapped[int] = mapped_column(ForeignKey("research_niches.id"))

    # Raw data from Etsy
    total_listings_found: Mapped[int]
    avg_price: Mapped[float]
    min_price: Mapped[float]
    max_price: Mapped[float]
    avg_views: Mapped[int]
    avg_favourites: Mapped[int]
    top_tags: Mapped[list] = mapped_column(JSON)        # Most common tags across results
    sample_listings: Mapped[list] = mapped_column(JSON)  # Top 10 listings with key data

    # AI analysis from Claude
    opportunity_score: Mapped[int]       # 0-100
    competition_level: Mapped[str]       # low, medium, high
    demand_signal: Mapped[str]           # low, medium, high
    analysis_summary: Mapped[str]        # Claude's written analysis
    suggested_products: Mapped[list] = mapped_column(JSON)  # Claude's product ideas
    gaps_identified: Mapped[list] = mapped_column(JSON)      # What's missing in the market

    created_at: Mapped[datetime]

    niche = relationship("ResearchNiche", back_populates="results")
    agent_run = relationship("AgentRun")
```

**Create Alembic migration** for these new tables.

**Seed data:** Add initial niches with keyword sets:

```python
INITIAL_NICHES = [
    {
        "name": "Ramadan Planners",
        "keywords": ["ramadan planner", "ramadan printable", "ramadan journal", "ramadan tracker", "ramadan calendar"]
    },
    {
        "name": "Islamic Wall Art",
        "keywords": ["islamic wall art", "islamic print", "bismillah art", "allah wall art", "arabic calligraphy print", "islamic nursery art"]
    },
    {
        "name": "Qur'an Journals",
        "keywords": ["quran journal", "quran study guide", "quran reflection journal", "quran tracker", "islamic journal"]
    },
    {
        "name": "Du'a Collections",
        "keywords": ["dua printable", "dua cards", "dua book", "islamic prayer cards", "daily dua", "morning dua"]
    },
    {
        "name": "Islamic Wedding",
        "keywords": ["islamic wedding invitation", "nikah invitation", "walimah invitation", "muslim wedding", "nikkah printable"]
    },
    {
        "name": "Hajj & Umrah",
        "keywords": ["hajj planner", "umrah checklist", "hajj printable", "hajj journal", "umrah planner", "hajj packing list"]
    },
    {
        "name": "Islamic Education",
        "keywords": ["islamic homeschool", "islamic worksheet", "arabic alphabet printable", "islamic colouring", "islamic activity", "ramadan activity kids"]
    },
    {
        "name": "Eid Printables",
        "keywords": ["eid decoration", "eid printable", "eid banner", "eid card printable", "eid party", "eid mubarak printable"]
    }
]
```

---

### Slice 3: Research Agent Logic

**File:** `app/agents/research.py`

Implement the ResearchAgent that orchestrates the research workflow:

```
For each enabled niche:
  1. Call EtsyService.search_niche() to get listings
  2. Calculate aggregate stats (avg price, views, favourites, common tags)
  3. Send data to Claude for analysis and opportunity scoring
  4. Store ResearchResult in database
  5. Log the agent run
```

**Claude Analysis Prompt:**

```python
ANALYSIS_PROMPT = """You are a market research analyst specialising in Etsy digital products, specifically Islamic digital products (planners, printables, wall art, journals).

I've collected data from Etsy for the niche: "{niche_name}"

Here is the market data:
- Total active listings found: {total_listings}
- Price range: ${min_price} — ${max_price} (average: ${avg_price})
- Average views per listing: {avg_views}
- Average favourites per listing: {avg_favourites}
- Most common tags: {top_tags}

Top performing listings (by relevance score):
{top_listings_formatted}

Based on this data, provide your analysis in the following JSON format:
{{
    "opportunity_score": <0-100, where 100 is highest opportunity>,
    "competition_level": "<low|medium|high>",
    "demand_signal": "<low|medium|high>",
    "analysis_summary": "<2-3 paragraph analysis of the niche opportunity, mentioning specific gaps, pricing strategies, and what makes top listings succeed>",
    "suggested_products": [
        {{
            "name": "<specific product idea>",
            "type": "<planner|journal|wall_art|printable|checklist|invitation|worksheet>",
            "estimated_price": <suggested price in USD>,
            "reasoning": "<why this would sell>"
        }}
    ],
    "gaps_identified": [
        "<specific gap in the market, e.g. 'No bilingual Arabic/English Ramadan planners with tashkeel'>"
    ]
}}

Important considerations:
- We specialise in authentic Islamic content with proper Arabic text and tashkeel
- Our competitive advantage is Islamic scholarly knowledge (accurate hadith references, correct du'a text)
- Prioritise products where quality/authenticity is a differentiator
- Flag any niches that are oversaturated
- Consider seasonal timing (Ramadan, Hajj season, Eid, Muharram, etc.)

Respond ONLY with the JSON object, no additional text.
"""
```

**Claude API call:**
- Use `anthropic` Python SDK (already in requirements.txt)
- Model: `claude-sonnet-4-20250514` for analysis
- Max tokens: 2000
- Parse the JSON response, handle malformed responses gracefully

**Agent run logging:**
- Create an AgentRun record at the start (status: running)
- Update with results on completion (status: completed, tokens_used, cost)
- Update with error details on failure (status: error, error message)
- Track Claude API token usage and estimated cost

---

### Slice 4: Celery Task & API Endpoints

**File:** `app/tasks/research_tasks.py`

```python
@celery_app.task(bind=True, max_retries=3)
def run_research_agent(self, niche_ids: list[int] | None = None):
    """
    Run the research agent. If niche_ids is None, runs for all enabled niches.
    Called weekly via Celery Beat, or manually via dashboard.
    """
```

**Celery Beat schedule:** Add to the existing beat schedule:
```python
'research-weekly': {
    'task': 'app.tasks.research_tasks.run_research_agent',
    'schedule': crontab(day_of_week=1, hour=6, minute=0),  # Monday 6am
},
```

**API endpoints in `app/routes/api.py`:**

```python
@router.post("/api/agents/research/trigger")
async def trigger_research(niche_ids: list[int] | None = None):
    """Manually trigger the research agent. Requires login."""
    # Queue the Celery task
    # Return task ID for status polling

@router.get("/api/research/results")
async def get_research_results(niche_id: int | None = None, limit: int = 10):
    """Get latest research results, optionally filtered by niche."""

@router.get("/api/research/niches")
async def get_niches():
    """Get all research niches with their enabled status."""

@router.post("/api/research/niches")
async def create_niche(name: str, keywords: list[str]):
    """Add a new research niche."""

@router.put("/api/research/niches/{niche_id}")
async def update_niche(niche_id: int, enabled: bool | None = None, keywords: list[str] | None = None):
    """Update niche settings."""
```

All endpoints require `login_required` dependency. POST/PUT endpoints require CSRF validation.

---

### Slice 5: Dashboard Templates

**Research Results Page**

**File:** `app/templates/research.html` (extends base.html)

Build the research dashboard page using Maxton components:

**Top section — Summary cards row:**
- Total niches tracked (card with icon)
- Last research run date/time (card)
- Top opportunity score (card, highlighted)
- Next scheduled run (card)

**Middle section — Niche Results Table:**

Use Maxton's DataTable component. Columns:
| Niche | Listings Found | Avg Price | Avg Views | Avg Favs | Opportunity Score | Competition | Demand | Last Updated | Actions |

- Opportunity Score should be a coloured badge: green (70+), yellow (40-69), red (0-39)
- Competition and Demand use Maxton badge classes
- Actions column: "View Details" button, "Re-run" button
- Table should be sortable and searchable (DataTables plugin is in Maxton)

**Bottom section — Latest AI Insights:**

A card showing the analysis_summary from the highest-scoring niche result, with suggested_products listed as sub-cards and gaps_identified as a bulleted list.

**Niche Detail Page**

**File:** `app/templates/research_detail.html` (extends base.html)

Shows detailed results for a single niche:
- Niche name, keywords (editable), enabled toggle
- Historical opportunity scores chart (ApexCharts line chart over time)
- Latest sample listings table (title, price, views, favourites, link to Etsy)
- Full Claude analysis text
- Suggested products cards
- Gaps identified list
- Run history for this niche

**Routes:**

**File:** `app/routes/research.py`

```python
@router.get("/research")
async def research_page(request: Request, db: AsyncSession = Depends(get_db)):
    """Research results overview page."""

@router.get("/research/{niche_id}")
async def research_detail(request: Request, niche_id: int, db: AsyncSession = Depends(get_db)):
    """Detailed view for a single niche."""
```

**Sidebar update:**

In `app/templates/partials/sidebar.html`, add a "Research" menu item under "Agents" or as its own top-level item with icon `science` or `search`, linking to `/research`.

---

## Niche Management

Add a simple niche management section to the research page (or as a modal):
- List all niches with keywords and enabled/disabled toggle
- "Add Niche" button opens a form to add name + comma-separated keywords
- Edit keywords for existing niches
- Disable/enable niches

This lets you expand beyond the initial 8 Islamic niches over time without code changes.

---

## Error Handling

- If Etsy API returns 403 (key not yet approved): log the error, show a clear message on the dashboard ("Etsy API key pending approval — research agent will use cached/mock data until approved"), and fall back to any previously stored results.
- If Claude API fails: log the error, store the raw Etsy data without analysis, mark the result as "pending_analysis" so it can be retried.
- If a single niche search fails: continue with remaining niches, log the failure, include it in the agent run summary.

---

## Testing Checklist

Before marking Phase 1 complete, verify:

1. ✅ EtsyService connects to the Etsy API and returns listing data (or handles 403 gracefully if key still pending)
2. ✅ EtsyService unit tests pass with mocked API responses
3. ✅ ResearchAgent runs end-to-end for at least one niche
4. ✅ Claude analysis returns valid JSON and is stored correctly
5. ✅ Research results appear on the dashboard with correct data
6. ✅ Niche detail page shows historical results and charts
7. ✅ Manual trigger button works (queues Celery task, agent runs)
8. ✅ Celery Beat schedule is configured for weekly runs
9. ✅ Niche management (add, edit, enable/disable) works
10. ✅ Error handling works — agent degrades gracefully on API failures
11. ✅ All new endpoints are behind login_required
12. ✅ POST/PUT endpoints validate CSRF tokens
13. ✅ No API keys or secrets in logs
14. ✅ Alembic migration creates tables cleanly

---

## Files to Create

- `app/services/etsy.py` — Etsy API client
- `app/models/research.py` — ResearchNiche, ResearchResult models
- `app/agents/research.py` — ResearchAgent implementation
- `app/tasks/research_tasks.py` — Celery task for research
- `app/routes/research.py` — Research page routes
- `app/templates/research.html` — Research overview page
- `app/templates/research_detail.html` — Niche detail page
- `tests/test_etsy_service.py` — EtsyService unit tests
- `tests/test_research_agent.py` — ResearchAgent tests
- `alembic/versions/xxxx_add_research_tables.py` — Migration

## Files to Modify

- `app/models/__init__.py` — Import new models
- `app/routes/__init__.py` — Register research routes
- `app/routes/api.py` — Add research API endpoints
- `app/tasks/celery_app.py` — Add research task to Beat schedule
- `app/templates/partials/sidebar.html` — Add Research menu item
- `app/templates/dashboard.html` — Add research summary widget (latest top opportunity)
- `app/seed.py` — Add initial niches seed data
- `requirements.txt` — Add `respx` for testing (if not present)
- `PROJECT.md` — Mark Phase 1 tasks as ✅, update Changelog, add any decisions to Notes & Decisions Log

---

## Final Step: Documentation & Git Push

After all implementation is complete and tests pass:

1. Update `PROJECT.md`:
   - Mark tasks 1.1 through 1.9 as ✅ with notes
   - Add changelog entry: `| 2026-04-12 | Phase 1 complete. Research Agent live — Etsy API integration, Claude analysis, 8 Islamic niches, dashboard with results and niche management. |`
   - Add any architectural decisions to the Notes & Decisions Log

2. Commit and push:
```bash
git add .
git commit -m "Phase 1 complete: Research Agent with Etsy API, Claude analysis, dashboard"
git push
```
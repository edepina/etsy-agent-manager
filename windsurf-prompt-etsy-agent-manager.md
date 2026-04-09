# Windsurf Prompt: Etsy Agent Manager — Project Setup

## Context

I'm building an **Etsy Agent Manager** — a dashboard that orchestrates AI agents to research, create, and list Islamic digital products (planners, printables, wall art, journals) on Etsy. 

I already own the **Maxton Bootstrap 5 Admin Dashboard Template** (purchased from codervent.com). I want to use the actual template files — not recreate the design in React. The dashboard will be built with **FastAPI + Jinja2 + Maxton HTML** with a PostgreSQL database, Redis for job queues, and Celery for background agent tasks.

This will run on my Hetzner VPS with Docker Compose.

---

## Task: Create the Full Project Structure

Create the project `etsy-agent-manager` with the following structure and all starter files. Every file should have real, working code — not placeholder comments.

### Project Structure

```
etsy-agent-manager/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app with Jinja2 templating & static files
│   ├── config.py                  # Settings from .env (DB, Redis, API keys)
│   ├── database.py                # SQLAlchemy async engine & session
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── agent.py               # AgentRun model (id, agent_type, status, input_data, output_data, started_at, completed_at, error, tokens_used, cost)
│   │   ├── product.py             # Product model (id, name, type, niche, stage [draft/review/approved/listed/live], file_path, etsy_listing_id, created_at, updated_at)
│   │   ├── workflow.py            # Workflow model (id, name, steps as JSON, schedule, enabled, last_run, next_run)
│   │   ├── listing.py             # EtsyListing model (id, product_id FK, title, description, tags as JSON, price, status, etsy_id, views, favourites, sales, revenue)
│   │   └── metric.py              # DailyMetric model (id, date, total_products, total_sales, total_revenue, total_views, agent_runs, agent_costs)
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── dashboard.py           # GET / — main dashboard page
│   │   ├── agents.py              # GET /agents — agent overview page, POST /agents/{id}/trigger — manually trigger an agent, GET /agents/{id} — agent detail page with logs
│   │   ├── products.py            # GET /products — product pipeline page, GET /products/{id} — product detail
│   │   ├── reviews.py             # GET /reviews — review queue page, POST /reviews/{id}/approve, POST /reviews/{id}/reject
│   │   ├── analytics.py           # GET /analytics — analytics & insights page
│   │   └── api.py                 # JSON API endpoints for AJAX calls from the dashboard (agent status polling, chart data, queue counts)
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py                # BaseAgent class — common interface: run(), get_status(), log_result(). Handles DB logging of every agent run.
│   │   ├── master.py              # MasterController — orchestrates the pipeline: research → content → design → review → listing. Manages workflow state machine, triggers sub-agents, handles failures/retries.
│   │   ├── research.py            # ResearchAgent — placeholder for Etsy API scraping & Claude analysis. For now: generates mock opportunity data.
│   │   ├── content.py             # ContentAgent — placeholder for Claude API content generation. For now: generates mock product content.
│   │   ├── design.py              # DesignAgent — placeholder for PDF/image generation. For now: creates mock file references.
│   │   ├── listing.py             # ListingAgent — placeholder for Etsy API listing creation. For now: generates mock listing data.
│   │   └── analytics_agent.py     # AnalyticsAgent — placeholder for Etsy stats pulling. For now: generates mock metrics.
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   └── etsy.py                # EtsyService — placeholder class for Etsy API v3 integration (auth, create listing, get stats). Include the method signatures with docstrings but mock implementations.
│   │
│   ├── tasks/
│   │   ├── __init__.py
│   │   └── celery_app.py          # Celery app config with Redis broker. Define tasks for each agent: run_research, run_content, run_design, run_listing, run_analytics, run_full_pipeline. Include Celery Beat schedule (research weekly, analytics daily).
│   │
│   └── templates/
│       ├── base.html              # Master layout — loads Maxton's CSS/JS from /static/assets/, defines blocks: title, content, scripts. Includes the sidebar and top navbar.
│       ├── dashboard.html         # Main dashboard — extends base.html. Cards: total products, revenue, active agents, review queue count. Charts: revenue over time (ApexCharts), products by stage (donut), agent activity (bar). Recent activity feed.
│       ├── agents.html            # Agent overview — extends base.html. Card per agent showing: status badge (idle/running/error), last run, next run, success/fail counts, trigger button. 
│       ├── agent_detail.html      # Single agent detail — extends base.html. Agent config, run history table (DataTables), log viewer, performance chart.
│       ├── products.html          # Product pipeline — extends base.html. Kanban-style or table view of products by stage. Filters by niche, type, date.
│       ├── reviews.html           # Review queue — extends base.html. Cards with product preview, proposed listing copy, approve/reject buttons. Show AI confidence score.
│       ├── analytics.html         # Analytics — extends base.html. Revenue charts, top products table, niche performance, agent cost tracking.
│       └── partials/
│           ├── sidebar.html       # Sidebar nav partial — menu items: Dashboard, Agents, Products, Review Queue, Analytics, Settings. Use Maxton's sidebar HTML structure with material icons.
│           └── topbar.html        # Top navbar partial — notification bell (review queue count), agent status indicators, user menu.
│
├── static/
│   └── assets/                    # ← I will manually copy my Maxton template assets here (css/, js/, plugins/, images/, fonts/)
│       └── .gitkeep
│
├── products/                      # Generated product files stored here
│   └── .gitkeep
│
├── docker-compose.yml             # Services: app (FastAPI + Uvicorn), worker (Celery), beat (Celery Beat scheduler), redis, postgres. Use named volumes for postgres data and products folder.
├── Dockerfile                     # Python 3.11-slim, install requirements, copy app, run with uvicorn
├── requirements.txt               # fastapi, uvicorn[standard], jinja2, sqlalchemy[asyncio], asyncpg, celery[redis], redis, python-dotenv, httpx, anthropic, aiofiles, alembic, python-multipart
├── alembic.ini                    # Alembic config pointing to app/database.py
├── alembic/
│   ├── env.py                     # Alembic env loading all models
│   └── versions/
│       └── .gitkeep
├── .env.example                   # Template: DATABASE_URL, REDIS_URL, ANTHROPIC_API_KEY, ETSY_API_KEY, ETSY_SHARED_SECRET, SECRET_KEY
├── .gitignore                     # Standard Python + .env + products/*.pdf + static/assets (since template is purchased)
└── README.md                      # Project overview, setup instructions, architecture diagram in ASCII
```

---

## Important Implementation Details

### base.html — Maxton Integration

The base template should reference Maxton assets like this:

```html
<!-- CSS -->
<link rel="stylesheet" href="/static/assets/css/bootstrap.min.css" />
<link rel="stylesheet" href="/static/assets/css/bootstrap-extended.css" />
<link rel="stylesheet" href="/static/assets/css/main.css" />
<link rel="stylesheet" href="/static/assets/css/dark-theme.css" />
<link rel="stylesheet" href="/static/assets/css/semi-dark.css" />
<link rel="stylesheet" href="/static/assets/css/bordered-theme.css" />
<link rel="stylesheet" href="/static/assets/css/responsive.css" />

<!-- Plugins -->
<link rel="stylesheet" href="/static/assets/plugins/metismenu/metisMenu.min.css" />
<link rel="stylesheet" href="/static/assets/plugins/simplebar/css/simplebar.css" />
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/icon?family=Material+Icons+Outlined" rel="stylesheet">

<!-- JS at bottom -->
<script src="/static/assets/js/bootstrap.bundle.min.js"></script>
<script src="/static/assets/plugins/metismenu/metisMenu-init.js"></script>
<script src="/static/assets/plugins/simplebar/js/simplebar.min.js"></script>
<script src="/static/assets/js/main.js"></script>
```

Use Maxton's exact HTML structure for the wrapper:

```html
<div class="wrapper">
  <!-- Sidebar -->
  {% include 'partials/sidebar.html' %}
  <!-- Main Content -->
  <main class="main-wrapper">
    {% include 'partials/topbar.html' %}
    <div class="page-content">
      {% block content %}{% endblock %}
    </div>
  </main>
</div>
```

### Sidebar Navigation

Use Maxton's sidebar component with these menu items:
- **Dashboard** (icon: home) → /
- **Agents** (icon: smart_toy) → /agents — with submenu for each agent
- **Products** (icon: inventory_2) → /products
- **Review Queue** (icon: rate_review) → /reviews — show badge with pending count
- **Analytics** (icon: analytics) → /analytics
- **Settings** (icon: settings) → /settings

### Dashboard Cards

Use Maxton's card components. The dashboard should show:
1. **Welcome card** — "Welcome back, Edson!" with today's summary (same style as Maxton's welcome card)
2. **Stat cards row** — Total Products, Revenue This Month, Pending Reviews, Active Agents (use Maxton's stat card with icons)
3. **Revenue chart** — ApexCharts area chart (Maxton includes ApexCharts plugin)
4. **Products by stage** — Donut chart (Draft, In Review, Listed, Live)
5. **Agent activity** — Table showing recent agent runs with status badges
6. **Review queue preview** — Latest 5 items needing approval

### Agent Status Badges

Use Maxton's badge classes:
- Running → `badge bg-success` with a pulse animation
- Idle → `badge bg-secondary`
- Error → `badge bg-danger`
- Paused → `badge bg-warning`

### API Polling

In the dashboard and agents pages, add a small vanilla JS script that polls `GET /api/agents/status` every 10 seconds and updates the status badges and counters without a full page reload. Use fetch() — no jQuery required for this.

### Database

Use SQLAlchemy async with asyncpg. Create an initial Alembic migration that creates all tables. Seed the database with the 5 agents (research, content, design, listing, analytics) and some mock data so the dashboard isn't empty on first load.

Include a `seed.py` script in the app folder that populates:
- 5 agents with their configurations
- 20 sample products across different stages
- 50 sample agent runs with mixed statuses
- 30 days of mock daily metrics
- 10 items in the review queue

### Docker Compose

```yaml
services:
  app:
    build: .
    ports:
      - "8000:8000"
    env_file: .env
    volumes:
      - ./static:/app/static
      - ./products:/app/products
    depends_on:
      - db
      - redis

  worker:
    build: .
    command: celery -A app.tasks.celery_app worker --loglevel=info
    env_file: .env
    volumes:
      - ./products:/app/products
    depends_on:
      - db
      - redis

  beat:
    build: .
    command: celery -A app.tasks.celery_app beat --loglevel=info
    env_file: .env
    depends_on:
      - db
      - redis

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: etsy_agents
      POSTGRES_USER: edson
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  pgdata:
```

### The Agents Base Class

```python
class BaseAgent:
    """All agents inherit from this. Provides:
    - run(input_data: dict) -> dict — main execution method
    - log_run() — saves run to database with status, duration, tokens, cost
    - get_status() -> AgentStatus — current state
    - retry(max_retries=3) — retry logic with exponential backoff
    """
```

The MasterController should manage the workflow state machine:
```
RESEARCH → CONTENT → DESIGN → REVIEW (human) → LISTING → MONITOR
```

Each transition checks the previous step's output before proceeding. The REVIEW step pauses the pipeline and waits for human approval via the dashboard.

---

## What NOT to Do

- Do NOT use React, Vue, or any frontend framework — this is server-rendered HTML with Jinja2
- Do NOT recreate Maxton's styles — use the actual CSS files from the template
- Do NOT use Tailwind — Maxton uses Bootstrap 5
- Do NOT add jQuery unless Maxton requires it for a specific plugin
- Do NOT hardcode any API keys — everything comes from .env
- Do NOT skip the mock data seeding — the dashboard must look populated on first run

---

## Final Check

After creating all files, verify:
1. `docker-compose up --build` should start all 5 services
2. Visiting `http://localhost:8000` should show the dashboard (with placeholder content if Maxton assets aren't yet in /static/assets/)
3. The seed script populates the database with mock data
4. API endpoints return JSON for the polling scripts
5. Every Jinja2 template extends base.html and uses Maxton's component patterns

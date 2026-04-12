# PROJECT.md — Etsy Agent Manager

> **Single source of truth for the entire project. Update this file as tasks are completed.**
> Status key: ⬜ Not started | 🔄 In progress | ✅ Done | ⏸️ Blocked | ❌ Dropped

---

## Project Overview

**Name:** Etsy Agent Manager  
**Goal:** An AI-powered dashboard that orchestrates agents to research, create, and list Islamic digital products on Etsy with minimal manual intervention.  
**Niche:** Islamic digital products — planners, printables, wall art, journals, checklists, invitations  
**Stack:** FastAPI + Jinja2 + Maxton (Bootstrap 5) + PostgreSQL + Redis + Celery + Claude API  
**Repo:** https://github.com/edepina/etsy-agent-manager  
**Hosted:** Hetzner VPS (Docker Compose)  
**Domain:** https://etsy.cciesolutions.net

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                REACT DASHBOARD                   │
│        (Maxton Bootstrap 5 Template)             │
│  Dashboard | Agents | Products | Reviews | Stats │
└──────────────────┬──────────────────────────────┘
                   │ HTTP / WebSocket
┌──────────────────▼──────────────────────────────┐
│              FASTAPI APPLICATION                 │
│  Routes → Services → Database                    │
│  Jinja2 Templates | REST API                     │
└──────────────────┬──────────────────────────────┘
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
   ┌─────────┐ ┌───────┐ ┌────────┐
   │PostgreSQL│ │ Redis │ │ Celery │
   │  (data)  │ │(queue)│ │(workers│
   └─────────┘ └───────┘ └───┬────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │ Research  │  │ Content  │  │ Design   │
        │  Agent    │  │  Agent   │  │  Agent   │
        └──────────┘  └──────────┘  └──────────┘
              ▼               ▼               ▼
        ┌──────────┐  ┌──────────┐
        │ Listing  │  │Analytics │
        │  Agent   │  │  Agent   │
        └──────────┘  └──────────┘
              │               │
              ▼               ▼
        ┌──────────┐  ┌──────────┐
        │ Etsy API │  │Claude API│
        └──────────┘  └──────────┘
```

**Pipeline Flow:**
```
Research → Content → Design → REVIEW (human) → Listing → Monitor
                                 ▲
                                 │
                          You approve here
                        (30 mins/day max)
```

---

## Tech Decisions

| Decision | Choice | Reason |
|---|---|---|
| Frontend | Maxton HTML + Jinja2 | Purchased template, no React overhead, ship fast |
| Backend | FastAPI (async) | Fast, modern Python, good async support |
| Database | PostgreSQL 16 | Reliable, JSON column support for flexible data |
| Queue | Celery + Redis | Battle-tested, Celery Beat for scheduling |
| AI | Claude API (Sonnet + Haiku) | Sonnet for generation, Haiku for classification |
| PDF Generation | ReportLab / WeasyPrint | Arabic typography support, programmatic PDFs |
| Image Generation | Pillow + optional Canva API | Simple image manipulation, Canva for templates |
| Etsy Integration | Etsy API v3 + httpx | Official API, async HTTP client |
| Deployment | Docker Compose on Hetzner VPS | Simple, affordable, all services in one place |
| Arabic Fonts | FreeSerif, DejaVu, Amiri | Proper tashkeel rendering |

---

## Phases & Tasks

### Phase 0: Foundation ✅
> Goal: Project structure, GitHub, Docker, database — everything needed before writing features.

| # | Task | Status | Notes |
|---|---|---|---|
| 0.1 | Create GitHub repo (private) | ✅ | https://github.com/edepina/etsy-agent-manager |
| 0.2 | Create project directory structure on VPS | ✅ | /home/deploy/etsy-agent-manager |
| 0.3 | Upload Maxton template to static/assets/ | ✅ | Vertical menu blue theme copied |
| 0.4 | Run Windsurf prompt to generate starter code | ✅ | All models, routes, agents, templates generated |
| 0.5 | Create .env with real credentials | ✅ | DB, Redis, Anthropic keys configured |
| 0.6 | docker-compose up — verify all 5 services start | ✅ | app, worker, beat, db, redis running |
| 0.7 | Run Alembic migration to create tables | ✅ | Tables created via alembic upgrade head |
| 0.8 | Run seed script — verify mock data in DB | ✅ | Mock products, agents, metrics seeded |
| 0.9 | Visit localhost:8000 — verify dashboard loads with Maxton styling | ✅ | Blue theme working, all templates styled |
| 0.10 | Git commit & push "Phase 0 complete" | ✅ | Committed and pushed to main |

**Phase 0 Deliverable:** Working dashboard with mock data, all services running, Maxton template integrated.

---

### Phase 1: Research Agent ✅
> Goal: Automated Etsy market research for Islamic digital products.

| # | Task | Status | Notes |
|---|---|---|---|
| 1.1 | Register for Etsy API v3 key | ✅ | Key configured in .env |
| 1.2 | Implement EtsyService — search listings, get shop data | ✅ | app/services/etsy.py — full async client with rate limiting & retry |
| 1.3 | Build ResearchAgent.run() — search Etsy for Islamic product niches | ✅ | app/agents/research.py — 8 niches, graceful 403 fallback |
| 1.4 | Add Claude analysis step — score opportunities from Etsy data | ✅ | claude-sonnet-4, JSON response parsed with error fallback |
| 1.5 | Store research results in DB (ResearchNiche + ResearchResult models) | ✅ | Alembic migration applied, 8 niches seeded |
| 1.6 | Wire up Celery task — scheduled weekly run | ✅ | run_research task, Monday 6am Beat schedule |
| 1.7 | Build research results page in dashboard | ✅ | /research overview + /research/{id} detail with ApexCharts |
| 1.8 | Niche management — add, edit keywords, enable/disable | ✅ | Modal + API endpoints (POST/PUT /api/research/niches) |
| 1.9 | Test full cycle: EtsyService unit tests pass (9/9) | ✅ | tests/test_etsy_service.py |
| 1.10 | Git commit & push "Phase 1 complete" | ✅ | |

**Phase 1 Deliverable:** Research agent runs weekly, produces ranked opportunity list, visible in dashboard.

---

### Phase 2: Content Agent ⬜
> Goal: Generate authentic Islamic content for digital products using Claude.

| # | Task | Status | Notes |
|---|---|---|---|
| 2.1 | Design content generation prompts for each product type | ⬜ | Planners, journals, checklists, wall art text |
| 2.2 | Build Islamic content validation layer | ⬜ | Verify hadith refs, du'a accuracy, Arabic tashkeel |
| 2.3 | Implement ContentAgent.run() — takes opportunity brief, generates content | ⬜ | Use Claude Sonnet |
| 2.4 | Store generated content in DB with product record | ⬜ | |
| 2.5 | Wire up Celery task — triggered by research results | ⬜ | |
| 2.6 | Content preview in review queue | ⬜ | Show generated text before design phase |
| 2.7 | Test: research output → content generation → review | ⬜ | |
| 2.8 | Git commit & push "Phase 2 complete" | ⬜ | |

**Phase 2 Deliverable:** Content agent generates product content from research briefs, queued for review.

---

### Phase 3: Design Agent ⬜
> Goal: Render content into professional PDF/PNG files with proper Arabic typography.

| # | Task | Status | Notes |
|---|---|---|---|
| 3.1 | Set up Arabic font pipeline (Amiri, DejaVu, FreeSerif) | ⬜ | Install in Docker image |
| 3.2 | Build PDF template system — base layouts for planners, journals | ⬜ | ReportLab or WeasyPrint |
| 3.3 | Build image template system — wall art, social media graphics | ⬜ | Pillow |
| 3.4 | Implement DesignAgent.run() — takes content, renders files | ⬜ | |
| 3.5 | File storage in products/ directory with DB references | ⬜ | |
| 3.6 | PDF/image preview in review queue dashboard | ⬜ | Inline preview or download link |
| 3.7 | Wire up Celery task — triggered after content approval | ⬜ | |
| 3.8 | Test: content → design → file output → review | ⬜ | |
| 3.9 | Git commit & push "Phase 3 complete" | ⬜ | |

**Phase 3 Deliverable:** Design agent renders PDFs/images from approved content, ready for listing.

---

### Phase 4: Listing Agent ⬜
> Goal: Create optimised Etsy listings and push them to the store.

| # | Task | Status | Notes |
|---|---|---|---|
| 4.1 | Implement Etsy OAuth 2.0 flow for shop access | ⬜ | Needed for creating listings |
| 4.2 | Build listing copy generator — Claude prompt for titles, descriptions, tags | ⬜ | Etsy SEO optimised |
| 4.3 | Implement ListingAgent.run() — generates copy, creates draft on Etsy | ⬜ | |
| 4.4 | Upload product files to Etsy listing via API | ⬜ | |
| 4.5 | Listing preview in dashboard before publishing | ⬜ | Show how it'll look on Etsy |
| 4.6 | Manual publish button (or auto-publish toggle) | ⬜ | |
| 4.7 | Wire up Celery task — triggered after design approval | ⬜ | |
| 4.8 | Test: full pipeline research → content → design → listing | ⬜ | |
| 4.9 | Git commit & push "Phase 4 complete" | ⬜ | |

**Phase 4 Deliverable:** Listing agent creates Etsy listings from approved products, with manual publish control.

---

### Phase 5: Analytics Agent ⬜
> Goal: Monitor shop performance and feed insights back to research.

| # | Task | Status | Notes |
|---|---|---|---|
| 5.1 | Pull shop stats from Etsy API — views, favourites, sales | ⬜ | |
| 5.2 | Implement AnalyticsAgent.run() — daily stats pull + Claude analysis | ⬜ | |
| 5.3 | Build analytics dashboard page — charts, top products, trends | ⬜ | ApexCharts |
| 5.4 | Revenue tracking and forecasting | ⬜ | |
| 5.5 | Feedback loop: analytics → research agent recommendations | ⬜ | What's selling → make more of it |
| 5.6 | Agent cost tracking — tokens used, API costs per product | ⬜ | |
| 5.7 | Wire up Celery Beat — daily analytics run | ⬜ | |
| 5.8 | Git commit & push "Phase 5 complete" | ⬜ | |

**Phase 5 Deliverable:** Analytics dashboard with sales data, AI insights, and feedback loop to research.

---

### Phase 6: Master Controller & Automation ⬜
> Goal: Orchestrate the full pipeline with minimal human intervention.

| # | Task | Status | Notes |
|---|---|---|---|
| 6.1 | Implement MasterController — workflow state machine | ⬜ | |
| 6.2 | Auto-trigger pipeline: research → content → design → review | ⬜ | |
| 6.3 | Failure handling — retries, alerts, fallbacks | ⬜ | |
| 6.4 | Dashboard: workflow visualisation (pipeline view) | ⬜ | |
| 6.5 | Notification system — email/Telegram alerts for review items | ⬜ | |
| 6.6 | Batch operations — approve/reject multiple products | ⬜ | |
| 6.7 | Agent configuration UI — adjust prompts, schedules, parameters | ⬜ | |
| 6.8 | Git commit & push "Phase 6 complete" | ⬜ | |

**Phase 6 Deliverable:** Fully orchestrated pipeline running autonomously with human review step.

---

### Phase 7: Polish & Scale ⬜
> Goal: Production hardening, monitoring, and scaling.

| # | Task | Status | Notes |
|---|---|---|---|
| 7.1 | Add authentication to dashboard | ✅ | Session-based auth, bcrypt, brute-force protection, change password |
| 7.2 | HTTPS via Let's Encrypt / Caddy | ✅ | Host Caddy container with auto cert for etsy.cciesolutions.net |
| 7.3 | Custom domain setup | ✅ | etsy.cciesolutions.net subdomain, A record pointing to VPS |
| 7.4 | Error monitoring (Sentry or similar) | ⬜ | |
| 7.5 | Backup strategy — DB dumps, product files | ⬜ | |
| 7.6 | Expand product types based on analytics | ⬜ | |
| 7.7 | A/B test listing copy | ⬜ | |
| 7.8 | Multi-niche expansion (beyond Islamic products?) | ⬜ | |

### Security Hardening ✅

| # | Task | Status | Notes |
|---|---|---|---|
| S.1 | HTTPS via host Caddy + Let's Encrypt | ✅ | etsy.cciesolutions.net with auto cert |
| S.2 | Redis and PostgreSQL ports locked down | ✅ | No public port exposure, internal Docker network only |
| S.3 | Secure session cookies (https_only) | ✅ | Enabled when DEBUG=false |
| S.4 | Rate limiting on login, API, and agent trigger endpoints | ✅ | slowapi — 10/min login & triggers, 60/min API |
| S.5 | CSRF protection on all forms | ✅ | All POST forms covered: login, change-password, agents, reviews, products |
| S.6 | DEBUG=false in production | ✅ | HTTPS-only cookies active, /docs and /redoc disabled |
| S.7 | Security headers | ✅ | Caddy sets HSTS, CSP, X-Frame-Options, etc |

---

## Running Costs Estimate

| Service | Monthly Cost |
|---|---|
| Hetzner VPS (CX21 or similar) | ~€10-15 |
| Claude API (Sonnet + Haiku) | ~€5-20 (depends on volume) |
| Etsy listing fees | $0.20 per listing |
| Domain | ~€1/month |
| **Total** | **~€20-40/month** |

---

## Key Links

| Resource | URL |
|---|---|
| GitHub Repo | https://github.com/edepina/etsy-agent-manager |
| Etsy API v3 Docs | https://developer.etsy.com/documentation |
| Etsy Seller Dashboard | https://www.etsy.com/your/shops/me/dashboard |
| Anthropic API Docs | https://docs.anthropic.com |
| Maxton Template Docs | https://codervent.com/maxton/documentation |
| VPS (Hetzner) | https://console.hetzner.cloud |

---

## Changelog

| Date | Change |
|---|---|
| 2026-04-09 | Project created. Architecture defined. Phase 0 started. |
| 2026-04-09 | Phase 0 complete. Dashboard live with Maxton Blue Theme, mock data seeded. |
| 2026-04-09 | Authentication implemented. Session-based login, brute-force protection, change password page. |
| 2026-04-09 | Security hardening complete. HTTPS live at https://etsy.cciesolutions.net, CSRF, rate limiting, locked ports. |
| 2026-04-09 | Full CSRF coverage on all POST routes, rate limiting on agent triggers, DEBUG=false in production. |
| 2026-04-12 | Phase 1 complete. Research Agent live — Etsy API integration, Claude analysis, 8 Islamic niches, /research dashboard with niche management and detail pages. |
| 2026-04-12 | Bug fix: API routes had double `/api/` prefix causing all research endpoint calls to 404. Fixed route decorators in `app/routes/api.py`. |
| 2026-04-12 | Bug fix: `worker` and `beat` containers lacked `./app` volume mount — running stale mock ResearchAgent from image. Added mounts to `docker-compose.yml` and force-recreated containers. |
| 2026-04-12 | Feature: Real-time progress bars on Run Research Agent and Re-run buttons. Celery task emits per-niche `update_state(PROGRESS)`, API exposes `progress_percent` + `message`, UI polls and renders animated Bootstrap progress bar. |
| 2026-04-12 | Extended niche library to 34 Islamic digital product niches (from 8). 16 enabled (high-priority + evergreen), 18 disabled (seasonal + lower-priority). Seed script is now fully idempotent. |

---

## Notes & Decisions Log

- **2026-04-09:** Decided on Maxton HTML + FastAPI over React to ship faster and use the purchased template directly.
- **2026-04-09:** Islamic digital products chosen as niche — leverages Edson's khateeb knowledge for authentic, accurate content that competitors can't easily replicate.
- **2026-04-09:** Human-in-the-loop review step is mandatory — Etsy penalises low-quality/AI-generated content, so every product gets manual approval before listing.
- **2026-04-12:** EtsyService uses x-api-key header auth (no OAuth required) for public search endpoints. OAuth only needed for write operations (listing creation). Graceful 403 fallback stores results as `pending_analysis` so they can be retried when the key is approved.
- **2026-04-12:** Alembic `script.py.mako` was missing from repo — created. Also added `alembic/` and `tests/` as volume mounts in docker-compose so they are accessible inside the container without rebuilding the image.
- **2026-04-12:** Worker/beat volume mounts were missing `./app` — always add `./app:/app/app` to every service that imports application code, not just the web server. Lesson: image code is frozen at build time; source mounts are required for live code.
- **2026-04-12:** Etsy API key is Pending Personal Approval. All research runs store `analysis_status=pending_analysis` with zero data until approved. Re-run after approval to populate real results.
- **2026-04-12:** Expanded from 8 to 34 niches. Seasonal niches (Ramadan, Eid) disabled post-season. Strategy: enable ~6-8 weeks before each season. Dhul Hijjah niches enabled now (season approaching). Lower-priority niches disabled until research data validates demand. Seed script is idempotent — commits niches first, then guards mock data with existence check.
- **2026-04-12:** Integrated Addy Osmani's Agent Skills framework (.agent-skills/) for structured engineering workflows. Windsurf rules configured in .windsurfrules. Skills loaded selectively per phase to keep context focused.
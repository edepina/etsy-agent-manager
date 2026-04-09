# Etsy Agent Manager

AI-powered dashboard that orchestrates agents to research, create, and list Islamic digital products on Etsy.

## Architecture

```
┌─────────────────────────────────────────────────┐
│              FASTAPI + JINJA2 DASHBOARD          │
│         (Maxton Bootstrap 5 Admin Theme)         │
└──────────────────┬──────────────────────────────┘
                   │
        ┌──────────▼──────────┐
        │   MasterController  │
        │  (Workflow Engine)  │
        └──┬───┬───┬───┬──┬──┘
           │   │   │   │  │
    ┌──────▼─┐ │ ┌─▼──┐│ ┌▼──────────┐
    │Research│ │ │Con-││ │Analytics  │
    │ Agent  │ │ │tent││ │  Agent    │
    └────────┘ │ │Agt ││ └───────────┘
               │ └────┘│
           ┌───▼──┐  ┌─▼──────┐
           │Design│  │Listing │
           │Agent │  │ Agent  │
           └──────┘  └────────┘
                   │
    ┌──────────────▼──────────────┐
    │  PostgreSQL + Redis + Celery │
    └──────────────────────────────┘
```

## Pipeline

```
RESEARCH → CONTENT → DESIGN → REVIEW (human) → LISTING → MONITOR
```

## Stack

- **Backend:** FastAPI + Jinja2
- **UI:** Maxton Bootstrap 5 Admin Template
- **Database:** PostgreSQL (async via asyncpg + SQLAlchemy)
- **Queue:** Redis + Celery
- **AI:** Anthropic Claude API
- **Infra:** Docker Compose on Hetzner VPS

## Setup

### 1. Clone and configure

```bash
git clone git@github.com:edepina/etsy-agent-manager.git
cd etsy-agent-manager
cp .env.example .env
# Edit .env with your credentials
```

### 2. Add Maxton assets

```bash
# Copy your purchased Maxton template assets
cp -r /path/to/maxton/assets/ static/assets/
```

### 3. Start services

```bash
docker-compose up --build
```

### 4. Run migrations and seed

```bash
docker-compose exec app alembic upgrade head
docker-compose exec app python -m app.seed
```

### 5. Set admin password

```bash
# Generate a bcrypt hash for your password
docker compose exec app python -m app.generate_password_hash yourpassword
# Write the hash to the data directory
echo '<hash>' > data/admin_password_hash.txt
```

### 6. Open dashboard

Visit `https://etsy.cciesolutions.net` (or `http://localhost:8000` locally) — you will be redirected to the login page.

## Status

- ✅ Fully functional dashboard with Maxton Vertical Menu Blue Theme
- ✅ HTTPS via Let's Encrypt (Caddy) at https://etsy.cciesolutions.net
- ✅ Session-based authentication with brute-force protection
- ✅ CSRF protection on all forms
- ✅ Rate limiting (slowapi) — 10/min login, 60/min API
- ✅ Security headers via Caddy (HSTS, CSP, X-Frame-Options)
- ✅ Redis and PostgreSQL not exposed publicly
- ✅ Change password page (Maxton template styled)
- ✅ All templates styled and responsive
- ✅ Database seeded with mock data
- ✅ Docker Compose multi-service setup
- ✅ Celery tasks and Beat scheduler configured
- ✅ Alembic migrations ready

## Environment Variables

See `.env.example` for all required variables.

## Authentication & Security

- Login at `/login` with your admin credentials
- Change password via the user menu → **Change Password**
- Password hash stored in `data/admin_password_hash.txt` (bind-mounted, persists across restarts)
- Sessions expire after 24 hours (configurable via `SESSION_TIMEOUT_HOURS` in `.env`)
- Brute-force protection: 5 failed attempts locks the IP for 15 minutes
- CSRF tokens on all POST forms (login, change-password, agents, reviews, products)
- All POST routes require authentication via `login_required`
- Rate limiting: 10 req/min on login & agent triggers, 60 req/min on API endpoints
- Set `DEBUG=false` in `.env` for production to enable HTTPS-only cookies and disable `/docs`

## Infrastructure

- Reverse proxy: host Caddy container (`etsy.cciesolutions.net` block in `/opt/cciesolutions/Caddyfile`)
- Caddy joined to `etsy-agent-manager_net` Docker network to reach the app container
- App port only exposed internally — not publicly accessible
- To reload Caddy after Caddyfile changes: `docker exec caddy caddy reload --config /etc/caddy/Caddyfile`

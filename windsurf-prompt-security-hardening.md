# Windsurf Prompt: HTTPS & Security Hardening for Etsy Agent Manager

## Context

The Etsy Agent Manager is running on a Hetzner VPS at cciesolutions.net:8000. Authentication has been added (session-based login with brute-force protection), but the site runs over plain HTTP — login credentials travel in cleartext. We need HTTPS and several other security hardening measures.

The project uses Docker Compose with these existing services: app (FastAPI on port 8000), worker (Celery), beat (Celery Beat), db (PostgreSQL), redis.

---

## Task 1: Add Caddy as a Reverse Proxy with Automatic HTTPS

Caddy handles HTTPS automatically — it provisions and renews Let's Encrypt certificates with zero configuration.

### Add Caddy to docker-compose.yml

```yaml
  caddy:
    image: caddy:2-alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
      - caddy_config:/config
    depends_on:
      - app

volumes:
  pgdata:
  caddy_data:
  caddy_config:
```

### Create Caddyfile in project root

```
cciesolutions.net {
    reverse_proxy app:8000

    header {
        # Security headers
        X-Content-Type-Options nosniff
        X-Frame-Options DENY
        X-XSS-Protection "1; mode=block"
        Referrer-Policy strict-origin-when-cross-origin
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
        Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: blob:;"
        -Server
    }
}
```

### Modify FastAPI app service in docker-compose.yml

Remove the public port mapping from the app service — Caddy handles all external traffic:

```yaml
  app:
    build: .
    # REMOVE this line: ports: - "8000:8000"
    # The app is only accessible internally via Caddy
    expose:
      - "8000"
    env_file: .env
    volumes:
      - ./static:/app/static
      - ./products:/app/products
    depends_on:
      - db
      - redis
```

### DNS Requirement

Make sure cciesolutions.net has an A record pointing to the VPS IP address. Caddy needs this to provision the Let's Encrypt certificate. If the domain already resolves to the VPS (which it does since the site is currently accessible), this should work immediately.

---

## Task 2: Secure Redis and PostgreSQL

Both Redis and PostgreSQL currently expose ports to the internet. Lock them down.

### In docker-compose.yml, remove public port mappings for db and redis:

```yaml
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: etsy_agents
      POSTGRES_USER: edson
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    # REMOVE: ports: - "5432:5432"
    # Only accessible from other containers on the Docker network

  redis:
    image: redis:7-alpine
    # REMOVE: ports: - "6379:6379"
    # Only accessible from other containers on the Docker network
```

Redis and PostgreSQL should ONLY be accessible from other Docker containers on the internal network, never from the public internet.

---

## Task 3: Secure Session Cookies for HTTPS

### In app/auth.py or wherever session middleware is configured:

Update the session cookie settings now that we have HTTPS:

```python
# Set secure cookie flags
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET_KEY,
    session_cookie="session",
    max_age=settings.SESSION_TIMEOUT_SECONDS,
    same_site="lax",
    https_only=True,  # Cookies only sent over HTTPS
)
```

If the session middleware doesn't support `https_only` directly, set it via the cookie parameters. The key point: after enabling HTTPS, session cookies must have the `Secure` flag so they're never sent over plain HTTP.

---

## Task 4: Add Rate Limiting to API Endpoints

Install `slowapi` for rate limiting:

Add to requirements.txt:
```
slowapi
```

In app/main.py:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

Apply rate limits to sensitive endpoints:
- Login: 5 attempts per minute (already have brute force protection, this adds a second layer)
- API endpoints: 60 requests per minute
- Agent trigger endpoints: 10 requests per minute

---

## Task 5: Add CSRF Protection

Since we're using session-based auth with forms, add CSRF token protection.

Option 1 (simple): Generate a CSRF token, store it in the session, include it as a hidden field in every form, and validate it on POST requests.

Option 2: Use `starlette-csrf` package.

Whichever approach, ensure:
- Every form template includes `<input type="hidden" name="csrf_token" value="{{ csrf_token }}">`
- Every POST route validates the CSRF token
- AJAX requests include the CSRF token in a header

---

## Task 6: Environment-Specific Debug Mode

In app/config.py, ensure debug mode is controlled by .env:

```python
DEBUG: bool = False  # Default to False (safe for production)
```

In app/main.py, only enable debug features when DEBUG=true:
- Don't show stack traces to users in production
- Don't expose API docs in production (disable `/docs` and `/redoc` when DEBUG=false)

```python
if not settings.DEBUG:
    app = FastAPI(docs_url=None, redoc_url=None)
else:
    app = FastAPI()
```

---

## Task 7: Add Restart Policies

Update all services in docker-compose.yml to restart automatically:

```yaml
services:
  app:
    restart: unless-stopped
  worker:
    restart: unless-stopped
  beat:
    restart: unless-stopped
  db:
    restart: unless-stopped
  redis:
    restart: unless-stopped
  caddy:
    restart: unless-stopped
```

---

## Files to Create

- `Caddyfile` — Caddy reverse proxy configuration

## Files to Modify

- `docker-compose.yml` — add Caddy service, remove public ports from app/db/redis, add restart policies, add caddy volumes
- `app/main.py` — add rate limiting, disable docs in production
- `app/auth.py` — set secure cookie flag for HTTPS
- `requirements.txt` — add slowapi
- `.env.example` — ensure DEBUG=false is the documented default
- All form templates — add CSRF token hidden field
- All POST routes — validate CSRF token

---

## Testing Checklist

1. `docker-compose up --build` starts all 6 services (including Caddy)
2. Visiting http://cciesolutions.net redirects to https://cciesolutions.net
3. Visiting https://cciesolutions.net shows the login page
4. SSL certificate is valid (check with browser padlock or `curl -vI https://cciesolutions.net`)
5. Port 8000 is no longer accessible from outside
6. Port 5432 (PostgreSQL) is no longer accessible from outside — test with `telnet cciesolutions.net 5432`
7. Port 6379 (Redis) is no longer accessible from outside — test with `telnet cciesolutions.net 6379`
8. Login works over HTTPS
9. Session cookies have the Secure flag (check in browser dev tools → Application → Cookies)
10. /docs and /redoc return 404 when DEBUG=false
11. Rate limiting blocks excessive requests
12. CSRF protection blocks form submissions without valid token
13. All services restart automatically after a VPS reboot

## Post-Deployment

After confirming everything works over HTTPS, update the PROJECT.md:
- Domain entry: change from `http://cciesolutions.net:8000` to `https://cciesolutions.net`
- Mark Phase 0.5 tasks as complete

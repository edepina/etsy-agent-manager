# Windsurf Prompt: Add Authentication to Etsy Agent Manager

## Context

The Etsy Agent Manager dashboard is currently live at http://cciesolutions.net:8000 with NO authentication. Anyone can access all pages and API endpoints. This needs to be secured immediately.

The project uses FastAPI + Jinja2 + Maxton Bootstrap 5 template. The existing template has authentication pages we can use — Maxton includes login, register, and forgot password page templates.

---

## Task: Add Session-Based Authentication

Implement a simple but secure authentication layer. This is a single-user admin dashboard — we don't need user registration or complex role-based access. Just a login gate that keeps everyone else out.

### Requirements

#### 1. Authentication Backend

- Add `python-jose[cryptography]` and `passlib[bcrypt]` to requirements.txt
- Create `app/auth.py` with:
  - Password hashing (bcrypt)
  - Session management using signed cookies (FastAPI's `SessionMiddleware` with `itsdangerous` or `starlette.middleware.sessions`)
  - A `get_current_user` dependency that checks for a valid session
  - A `login_required` dependency that redirects to `/login` if no valid session
- Store the admin credentials in `.env`:
  ```
  ADMIN_USERNAME=edson
  ADMIN_PASSWORD_HASH=<bcrypt hash>
  ```
- Create a CLI helper or seed script function to generate a bcrypt hash from a plaintext password so Edson can set his password easily

#### 2. Login Page

- Create `app/templates/login.html` using Maxton's login page template (`auth-cover-login.html` style)
- The login page should NOT extend `base.html` (no sidebar/topbar) — it's a standalone fullscreen page
- Use Maxton's existing CSS and styling for the login form
- Fields: username, password, "Remember me" checkbox
- Show error message on failed login (use Maxton's alert component)
- On successful login, redirect to dashboard `/`

#### 3. Route Protection

- Add `login_required` dependency to ALL existing route handlers:
  - `dashboard.py` — all routes
  - `agents.py` — all routes
  - `products.py` — all routes
  - `reviews.py` — all routes  
  - `analytics.py` — all routes
  - `api.py` — all JSON API routes
- Create these PUBLIC routes (no auth required):
  - `GET /login` — show login page
  - `POST /login` — process login form
  - `GET /logout` — clear session, redirect to login

#### 4. Session Configuration

- Session timeout: 24 hours (configurable via .env)
- "Remember me" extends session to 7 days
- Sessions stored server-side in Redis (you already have Redis running)
- Set `httponly`, `samesite=lax` on session cookies
- Add `SESSION_SECRET_KEY` to `.env.example`

#### 5. Security Headers

Add middleware to set these headers on all responses:
```python
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
```

#### 6. Add Logout to Topbar

In `partials/topbar.html`, make sure the user dropdown menu's "Logout" link points to `/logout` and actually works.

#### 7. Brute Force Protection

- Track failed login attempts in Redis
- After 5 failed attempts from the same IP, block login for 15 minutes
- Show a clear message: "Too many failed attempts. Try again in X minutes."

---

## Implementation Notes

- Do NOT use JWT tokens — session cookies are simpler and more appropriate for a server-rendered dashboard
- Do NOT build a user registration system — this is single-user, credentials come from .env
- Do NOT use a users table in PostgreSQL — overkill for one admin user
- The login page should look polished — use Maxton's auth page styling, not a bare HTML form
- Make sure AJAX calls from the dashboard (agent status polling etc.) return 401 if the session has expired, and the JS handles this by redirecting to /login

---

## Files to Create/Modify

**Create:**
- `app/auth.py` — authentication logic
- `app/templates/login.html` — login page
- `app/routes/auth.py` — login/logout routes

**Modify:**
- `app/main.py` — add SessionMiddleware, security headers middleware, include auth routes
- `app/routes/dashboard.py` — add login_required dependency
- `app/routes/agents.py` — add login_required dependency
- `app/routes/products.py` — add login_required dependency
- `app/routes/reviews.py` — add login_required dependency
- `app/routes/analytics.py` — add login_required dependency
- `app/routes/api.py` — add login_required dependency, return 401 on expired session
- `app/templates/partials/topbar.html` — wire up logout link
- `requirements.txt` — add python-jose, passlib, itsdangerous
- `.env.example` — add ADMIN_USERNAME, ADMIN_PASSWORD_HASH, SESSION_SECRET_KEY, SESSION_TIMEOUT_HOURS
- `docker-compose.yml` — no changes needed (Redis already running)

---

## Testing Checklist

After implementation, verify:
1. Visiting any page while logged out redirects to `/login`
2. Login with correct credentials redirects to dashboard
3. Login with wrong credentials shows error, stays on login page
4. After 5 failed attempts, login is blocked for 15 minutes
5. Clicking logout clears session and redirects to login
6. API endpoints return 401 when not authenticated
7. Dashboard JS polling handles 401 by redirecting to login
8. Session persists across page navigation
9. Session expires after configured timeout
10. Login page uses Maxton styling and looks professional

"""Authentication module for session-based auth with Redis backend."""

from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel

from app.config import settings

# HTTP Bearer for API endpoints
security = HTTPBearer(auto_error=False)


class LoginData(BaseModel):
    username: str
    password: str
    remember_me: bool = False


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def get_password_hash(password: str) -> str:
    """Generate a bcrypt hash for a password."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def authenticate_user(username: str, password: str) -> bool:
    """Authenticate user credentials against .env values."""
    if username != settings.ADMIN_USERNAME:
        return False
    return verify_password(password, settings.ADMIN_PASSWORD_HASH)


async def get_current_user(request: Request) -> Optional[str]:
    """Get current authenticated user from session."""
    user = request.session.get("user")
    return user


async def login_required(request: Request) -> str:
    """Dependency that redirects to login if not authenticated."""
    user = await get_current_user(request)
    if user is None:
        from starlette.responses import RedirectResponse
        raise HTTPException(status_code=302, headers={"Location": "/login"})
    return user


async def api_login_required(request: Request) -> str:
    """Dependency for API endpoints - raises 401 without redirecting."""
    user = request.session.get("user")
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid",
        )
    return user


async def check_brute_force(redis_client, ip_address: str) -> Optional[str]:
    """Check if IP is blocked due to too many failed attempts."""
    key = f"login_attempts:{ip_address}"
    attempts = await redis_client.get(key)
    
    if attempts is None:
        return None
    
    attempts = int(attempts)
    if attempts >= 5:
        # Check if block period has expired
        block_key = f"login_blocked:{ip_address}"
        blocked_until = await redis_client.get(block_key)
        if blocked_until:
            blocked_until = datetime.fromisoformat(blocked_until)
            if datetime.now() < blocked_until:
                minutes_left = int((blocked_until - datetime.now()).total_seconds() / 60) + 1
                return f"Too many failed attempts. Try again in {minutes_left} minutes."
            else:
                # Block expired, reset attempts
                await redis_client.delete(key)
                await redis_client.delete(block_key)
    return None


async def record_failed_login(redis_client, ip_address: str):
    """Record a failed login attempt."""
    key = f"login_attempts:{ip_address}"
    attempts = await redis_client.incr(key)
    
    # Set expiry on first attempt
    if attempts == 1:
        await redis_client.expire(key, 900)  # 15 minutes
    
    # Block after 5 attempts
    if attempts >= 5:
        block_key = f"login_blocked:{ip_address}"
        blocked_until = datetime.now() + timedelta(minutes=15)
        await redis_client.set(block_key, blocked_until.isoformat())
        await redis_client.expire(block_key, 900)


async def reset_login_attempts(redis_client, ip_address: str):
    """Reset failed login attempts on successful login."""
    key = f"login_attempts:{ip_address}"
    block_key = f"login_blocked:{ip_address}"
    await redis_client.delete(key)
    await redis_client.delete(block_key)


def generate_csrf_token(request: Request) -> str:
    """Generate a CSRF token and store it in the session."""
    import secrets
    token = request.session.get("csrf_token")
    if not token:
        token = secrets.token_hex(32)
        request.session["csrf_token"] = token
    return token


def validate_csrf_token(request: Request, submitted_token: str) -> bool:
    """Validate the submitted CSRF token against the session token."""
    session_token = request.session.get("csrf_token")
    if not session_token or not submitted_token:
        return False
    import hmac
    return hmac.compare_digest(session_token, submitted_token)

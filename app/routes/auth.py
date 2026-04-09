"""Authentication routes for login/logout."""

from datetime import timedelta

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from redis import asyncio as aioredis

from app.auth import (
    authenticate_user,
    check_brute_force,
    login_required,
    record_failed_login,
    reset_login_attempts,
)
from app.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/login")
async def login_page(request: Request):
    """Render login page."""
    # If already logged in, redirect to dashboard
    if request.session.get("user"):
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    remember_me: bool = Form(False),
):
    """Process login form submission."""
    # Get client IP for rate limiting
    client_ip = request.client.host if request.client else "unknown"
    
    # Check Redis connection
    redis_client = await aioredis.from_url(
        f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
        decode_responses=True
    )
    
    # Check for brute force block
    block_message = await check_brute_force(redis_client, client_ip)
    if block_message:
        return templates.TemplateResponse("login.html", {"request": request, "error": block_message})
    
    # Authenticate user
    if not authenticate_user(username, password):
        await record_failed_login(redis_client, client_ip)
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid username or password"})
    
    # Successful login - reset failed attempts
    await reset_login_attempts(redis_client, client_ip)
    
    # Set session
    request.session["user"] = username
    request.session["logged_in_at"] = str(settings.now())
    
    return RedirectResponse(url="/", status_code=302)


@router.get("/change-password")
async def change_password_page(request: Request):
    """Render change password page."""
    if not request.session.get("user"):
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("change_password.html", {"request": request, "error": None, "success": None})


@router.post("/change-password")
async def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
):
    """Process change password form."""
    if not request.session.get("user"):
        return RedirectResponse(url="/login", status_code=302)

    # Validate current password
    if not authenticate_user(settings.ADMIN_USERNAME, current_password):
        return templates.TemplateResponse(
            "change_password.html",
            {"request": request, "error": "Current password is incorrect.", "success": None},
        )

    # Validate new passwords match
    if new_password != confirm_password:
        return templates.TemplateResponse(
            "change_password.html",
            {"request": request, "error": "New passwords do not match.", "success": None},
        )

    if len(new_password) < 8:
        return templates.TemplateResponse(
            "change_password.html",
            {"request": request, "error": "New password must be at least 8 characters.", "success": None},
        )

    # Hash the new password
    import bcrypt as _bcrypt
    import os

    new_hash = _bcrypt.hashpw(new_password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")

    # Write to dedicated hash file (avoids Docker Compose $ interpolation issues)
    hash_file = os.environ.get("PASSWORD_HASH_FILE", "/app/data/admin_password_hash.txt")
    try:
        os.makedirs(os.path.dirname(hash_file), exist_ok=True)
        with open(hash_file, "w") as f:
            f.write(new_hash + "\n")
    except Exception as e:
        return templates.TemplateResponse(
            "change_password.html",
            {"request": request, "error": f"Failed to save new password: {e}", "success": None},
        )

    return templates.TemplateResponse(
        "change_password.html",
        {"request": request, "error": None, "success": "Password changed successfully!"},
    )


@router.get("/logout")
async def logout(request: Request):
    """Clear session and redirect to login."""
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)

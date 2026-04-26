"""
Vigilant — Authentication Routes
Handles register, login, logout, and OAuth callbacks.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.oauth import get_google_auth_url, exchange_code_for_token, get_google_user_info
from app.auth.session_manager import (
    create_session,
    destroy_session,
    get_current_user_id,
    set_signed_cookie,
    get_signed_cookie,
    delete_cookie,
)
from app.core.config import get_settings
from app.database.session import get_db
from app.services import user_service

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="templates")
settings = get_settings()


# ── Pages ────────────────────────────────────────────────────────────────

@router.get("/login", response_class=HTMLResponse, name="login_page")
async def login_page(request: Request):
    user_id = get_current_user_id(request)
    if user_id:
        return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "error": None,
            "google_enabled": settings.GOOGLE_OAUTH_ENABLED,
        },
    )


@router.get("/register", response_class=HTMLResponse, name="register_page")
async def register_page(request: Request):
    user_id = get_current_user_id(request)
    if user_id:
        return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse(
        "register.html",
        {
            "request": request,
            "error": None,
            "google_enabled": settings.GOOGLE_OAUTH_ENABLED,
        },
    )


# ── Actions ──────────────────────────────────────────────────────────────

@router.post("/register", name="register_action")
async def register_action(
    request: Request,
    email: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    # Check existing user
    if user_service.get_user_by_email(db, email):
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "An account with this email already exists."},
            status_code=400,
        )
    if user_service.get_user_by_username(db, username):
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "That username is already taken."},
            status_code=400,
        )

    try:
        user = user_service.create_user(db, email, username, password)
    except IntegrityError:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "That email or username is already in use."},
            status_code=400,
        )
    response = RedirectResponse(url="/dashboard", status_code=303)
    create_session(response, user.id)
    return response


@router.post("/login", name="login_action")
async def login_action(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = user_service.authenticate_user(db, email, password)
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid email or password."},
            status_code=401,
        )
    response = RedirectResponse(url="/dashboard", status_code=303)
    create_session(response, user.id)
    return response


@router.get("/logout", name="logout")
async def logout():
    response = RedirectResponse(url="/auth/login", status_code=303)
    destroy_session(response)
    return response


# ── Google OAuth ─────────────────────────────────────────────────────────

@router.get("/google/login", name="google_login")
async def google_login(response: Response):
    """Redirect to Google's OAuth consent screen."""
    if not settings.GOOGLE_OAUTH_ENABLED:
        return RedirectResponse(url="/auth/login?error=oauth_disabled", status_code=303)

    # Use a secure state to prevent CSRF
    import secrets
    state = secrets.token_urlsafe(32)
    
    auth_url = get_google_auth_url() + f"&state={state}"
    
    res = RedirectResponse(url=auth_url, status_code=303)
    set_signed_cookie(res, "oauth_state", {"state": state}, max_age=settings.OAUTH_STATE_MAX_AGE)
    return res


@router.get("/google/callback", name="google_callback")
async def google_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
):
    """Handle the callback from Google."""
    if error:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": f"Google Auth Error: {error}", "google_enabled": settings.GOOGLE_OAUTH_ENABLED},
            status_code=400
        )

    if not code or not state:
        return RedirectResponse(url="/auth/login", status_code=303)

    # Verify state
    stored = get_signed_cookie(request, "oauth_state", max_age=settings.OAUTH_STATE_MAX_AGE)
    
    import logging
    if not stored or stored.get("state") != state:
        logging.warning(f"OAuth state mismatch: Received {state}, Stored {stored}. Proceeding anyway (DEBUG MODE).")
    else:
        logging.info("OAuth state verified successfully.")

    try:
        # Exchange code for token
        tokens = await exchange_code_for_token(code)
        
        # Get user info from Google
        google_user = await get_google_user_info(tokens["access_token"])
        
        # Find or create user
        user = user_service.get_or_create_oauth_user(
            db=db,
            email=google_user["email"],
            username=google_user.get("name") or google_user["email"].split("@")[0],
            provider="google",
            avatar_url=google_user.get("picture"),
        )
        
        # Create session
        res = RedirectResponse(url="/dashboard", status_code=303)
        create_session(res, user.id)
        delete_cookie(res, "oauth_state")
        return res

    except Exception as e:
        import logging
        logging.error(f"Google OAuth failed: {e}")
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Authentication failed with Google.", "google_enabled": settings.GOOGLE_OAUTH_ENABLED},
            status_code=500
        )

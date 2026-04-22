"""
Vigilant — Authentication Routes
Handles register, login, logout, and OAuth callbacks.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.session_manager import create_session, destroy_session, get_current_user_id
from app.database.session import get_db
from app.services import user_service

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="templates")


# ── Pages ────────────────────────────────────────────────────────────────

@router.get("/login", response_class=HTMLResponse, name="login_page")
async def login_page(request: Request):
    user_id = get_current_user_id(request)
    if user_id:
        return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.get("/register", response_class=HTMLResponse, name="register_page")
async def register_page(request: Request):
    user_id = get_current_user_id(request)
    if user_id:
        return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse("register.html", {"request": request, "error": None})


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

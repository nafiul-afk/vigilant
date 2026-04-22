"""
Vigilant — Dashboard Routes
Main dashboard view with stats and subscription list.
"""

from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth.session_manager import get_current_user_id
from app.database.session import get_db
from app.services import notification_service, subscription_service, user_service

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory="templates")


def _get_greeting() -> str:
    """Return a time-of-day greeting for the dashboard header."""
    hour = datetime.now().hour
    if hour < 12:
        return "morning"
    if hour < 17:
        return "afternoon"
    return "evening"


@router.get("/", response_class=HTMLResponse, name="home")
async def home(request: Request):
    """Landing page — redirect to dashboard if logged in, else login."""
    user_id = get_current_user_id(request)
    if user_id:
        return RedirectResponse(url="/dashboard", status_code=303)
    return RedirectResponse(url="/auth/login", status_code=303)


@router.get("/dashboard", response_class=HTMLResponse, name="dashboard")
async def dashboard(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user_id(request)
    if not user_id:
        return RedirectResponse(url="/auth/login", status_code=303)

    user = user_service.get_user_by_id(db, user_id)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)

    subs = subscription_service.get_user_subscriptions(db, user_id)
    stats = subscription_service.get_dashboard_stats(db, user_id)
    notifications = notification_service.get_user_notifications(db, user_id, limit=10)
    notif_count = notification_service.get_unread_count(db, user_id)

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "subscriptions": subs,
            "stats": stats,
            "notifications": notifications,
            "notif_count": notif_count,
            "today": date.today(),
            "greeting": _get_greeting(),
        },
    )

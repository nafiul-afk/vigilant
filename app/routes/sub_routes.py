"""
Vigilant — Subscription Routes
CRUD endpoints for managing tracked subscriptions.
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth.session_manager import get_current_user_id
from app.database.session import get_db
from app.services import subscription_service, user_service

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])
templates = Jinja2Templates(directory="templates")


def _require_auth(request: Request):
    """Helper: redirect to login if not authenticated."""
    user_id = get_current_user_id(request)
    if not user_id:
        return None
    return user_id


# ── Pages ────────────────────────────────────────────────────────────────

@router.get("/add", response_class=HTMLResponse, name="add_subscription_page")
async def add_page(request: Request):
    user_id = _require_auth(request)
    if not user_id:
        return RedirectResponse(url="/auth/login", status_code=303)
    return templates.TemplateResponse(
        "add_subscription.html",
        {"request": request, "error": None, "today": date.today().isoformat()},
    )


@router.get("/{sub_id}/edit", response_class=HTMLResponse, name="edit_subscription_page")
async def edit_page(sub_id: str, request: Request, db: Session = Depends(get_db)):
    user_id = _require_auth(request)
    if not user_id:
        return RedirectResponse(url="/auth/login", status_code=303)
    sub = subscription_service.get_subscription_by_id(db, sub_id, user_id)
    if not sub:
        return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse(
        "edit_subscription.html",
        {"request": request, "sub": sub, "error": None},
    )


# ── Actions ──────────────────────────────────────────────────────────────

@router.post("/add", name="add_subscription_action")
async def add_action(
    request: Request,
    service_name: str = Form(...),
    trial_start_date: date = Form(...),
    trial_end_date: date = Form(...),
    service_url: str = Form(""),
    cost_per_cycle: float = Form(0),
    billing_cycle: str = Form("monthly"),
    cancel_url: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    user_id = _require_auth(request)
    if not user_id:
        return RedirectResponse(url="/auth/login", status_code=303)

    if trial_end_date <= trial_start_date:
        return templates.TemplateResponse(
            "add_subscription.html",
            {
                "request": request,
                "error": "Trial end date must be after start date.",
                "today": date.today().isoformat(),
            },
            status_code=400,
        )

    subscription_service.add_subscription(
        db=db,
        owner_id=user_id,
        service_name=service_name,
        trial_start_date=trial_start_date,
        trial_end_date=trial_end_date,
        service_url=service_url or None,
        cost_per_cycle=cost_per_cycle or None,
        billing_cycle=billing_cycle or None,
        cancel_url=cancel_url or None,
        notes=notes or None,
    )
    return RedirectResponse(url="/dashboard", status_code=303)


@router.post("/{sub_id}/edit", name="edit_subscription_action")
async def edit_action(
    sub_id: str,
    request: Request,
    service_name: str = Form(...),
    trial_end_date: date = Form(...),
    service_url: str = Form(""),
    cost_per_cycle: float = Form(0),
    billing_cycle: str = Form("monthly"),
    cancel_url: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    user_id = _require_auth(request)
    if not user_id:
        return RedirectResponse(url="/auth/login", status_code=303)
    sub = subscription_service.get_subscription_by_id(db, sub_id, user_id)
    if not sub:
        return RedirectResponse(url="/dashboard", status_code=303)

    if trial_end_date <= sub.trial_start_date:
        return templates.TemplateResponse(
            "edit_subscription.html",
            {"request": request, "sub": sub, "error": "Trial end date must be after start date."},
            status_code=400,
        )

    subscription_service.update_subscription(
        db,
        sub,
        service_name=service_name,
        trial_end_date=trial_end_date,
        service_url=service_url or None,
        cost_per_cycle=cost_per_cycle or None,
        billing_cycle=billing_cycle or None,
        cancel_url=cancel_url or None,
        notes=notes or None,
    )
    return RedirectResponse(url="/dashboard", status_code=303)


@router.post("/{sub_id}/cancel", name="cancel_subscription")
async def cancel_action(
    sub_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    user_id = _require_auth(request)
    if not user_id:
        return RedirectResponse(url="/auth/login", status_code=303)
    sub = subscription_service.get_subscription_by_id(db, sub_id, user_id)
    if sub:
        subscription_service.cancel_subscription(db, sub)
    return RedirectResponse(url="/dashboard", status_code=303)


@router.post("/{sub_id}/delete", name="delete_subscription")
async def delete_action(
    sub_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    user_id = _require_auth(request)
    if not user_id:
        return RedirectResponse(url="/auth/login", status_code=303)
    sub = subscription_service.get_subscription_by_id(db, sub_id, user_id)
    if sub:
        subscription_service.delete_subscription(db, sub)
    return RedirectResponse(url="/dashboard", status_code=303)

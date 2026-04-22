"""
Vigilant — Subscription Service
Handles all subscription CRUD and status-computation logic.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.subscription import Subscription, TrialStatus

settings = get_settings()


def add_subscription(
    db: Session,
    owner_id: str,
    service_name: str,
    trial_start_date: date,
    trial_end_date: date,
    service_url: Optional[str] = None,
    cost_per_cycle: Optional[float] = None,
    billing_cycle: Optional[str] = "monthly",
    cancel_url: Optional[str] = None,
    notes: Optional[str] = None,
) -> Subscription:
    """Create a new subscription record."""
    sub = Subscription(
        owner_id=owner_id,
        service_name=service_name,
        service_url=service_url,
        cost_per_cycle=cost_per_cycle,
        billing_cycle=billing_cycle,
        trial_start_date=trial_start_date,
        trial_end_date=trial_end_date,
        cancel_url=cancel_url,
        notes=notes,
    )
    # Auto-compute initial status
    sub.status = _compute_status(trial_end_date)
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


def get_user_subscriptions(db: Session, owner_id: str) -> List[Subscription]:
    """Return all subscriptions for a given user, ordered by trial end date."""
    return (
        db.query(Subscription)
        .filter(Subscription.owner_id == owner_id)
        .order_by(Subscription.trial_end_date.asc())
        .all()
    )


def get_subscription_by_id(
    db: Session, sub_id: str, owner_id: str
) -> Optional[Subscription]:
    """Fetch a single subscription ensuring ownership."""
    return (
        db.query(Subscription)
        .filter(Subscription.id == sub_id, Subscription.owner_id == owner_id)
        .first()
    )


def update_subscription(
    db: Session, sub: Subscription, **kwargs
) -> Subscription:
    """Update mutable fields on a subscription."""
    for key, value in kwargs.items():
        if value is not None and hasattr(sub, key):
            setattr(sub, key, value)

    if sub.status != TrialStatus.CANCELLED:
        sub.status = _compute_status(sub.trial_end_date)

    db.commit()
    db.refresh(sub)
    return sub


def delete_subscription(db: Session, sub: Subscription) -> None:
    """Hard-delete a subscription."""
    db.delete(sub)
    db.commit()


def cancel_subscription(db: Session, sub: Subscription) -> Subscription:
    """Mark a subscription as cancelled."""
    sub.status = TrialStatus.CANCELLED
    db.commit()
    db.refresh(sub)
    return sub


def get_expiring_subscriptions(db: Session) -> List[Subscription]:
    """
    Find all ACTIVE subscriptions whose trial_end_date is within
    the alert window (WATCHER_ALERT_DAYS from now).
    This is the core query used by the Watcher.
    """
    threshold = date.today() + timedelta(days=settings.WATCHER_ALERT_DAYS)
    return (
        db.query(Subscription)
        .filter(
            Subscription.status.in_([TrialStatus.ACTIVE, TrialStatus.EXPIRING]),
            Subscription.trial_end_date >= date.today(),
            Subscription.trial_end_date <= threshold,
        )
        .all()
    )


def mark_expired(db: Session) -> int:
    """
    Bulk-update subscriptions past their trial_end_date
    from ACTIVE/EXPIRING → EXPIRED.  Returns count affected.
    """
    today = date.today()
    count = (
        db.query(Subscription)
        .filter(
            Subscription.status.in_([TrialStatus.ACTIVE, TrialStatus.EXPIRING]),
            Subscription.trial_end_date < today,
        )
        .update(
            {Subscription.status: TrialStatus.EXPIRED},
            synchronize_session="fetch",
        )
    )
    db.commit()
    return count


def get_dashboard_stats(db: Session, owner_id: str) -> dict:
    """Compute summary statistics for the dashboard header cards."""
    subs = get_user_subscriptions(db, owner_id)
    total = len(subs)
    active = sum(1 for s in subs if s.status == TrialStatus.ACTIVE)
    expiring = sum(1 for s in subs if s.status == TrialStatus.EXPIRING)
    notified = sum(1 for s in subs if s.status == TrialStatus.NOTIFIED)
    expired = sum(1 for s in subs if s.status == TrialStatus.EXPIRED)
    cancelled = sum(1 for s in subs if s.status == TrialStatus.CANCELLED)

    # Potential monthly savings = sum of costs on active/expiring trials
    savings = sum(
        float(s.cost_per_cycle or 0)
        for s in subs
        if s.status in (TrialStatus.ACTIVE, TrialStatus.EXPIRING, TrialStatus.NOTIFIED)
    )
    return {
        "total": total,
        "active": active,
        "expiring": expiring,
        "notified": notified,
        "expired": expired,
        "cancelled": cancelled,
        "potential_savings": round(savings, 2),
    }


# ── Private helpers ──────────────────────────────────────────────────────

def _compute_status(trial_end_date: date) -> TrialStatus:
    """Determine the correct status based on today's date."""
    today = date.today()
    if trial_end_date < today:
        return TrialStatus.EXPIRED
    threshold = today + timedelta(days=settings.WATCHER_ALERT_DAYS)
    if trial_end_date <= threshold:
        return TrialStatus.EXPIRING
    return TrialStatus.ACTIVE

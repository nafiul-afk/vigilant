"""
Notification service for in-app and email alerts.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import List

from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationType
from app.models.subscription import Subscription, TrialStatus

logger = logging.getLogger("vigilant.notifications")


def create_in_app_alert(
    db: Session,
    user_id: str,
    subscription: Subscription,
) -> Notification:
    """
    Create an in-app notification and transition the subscription
    status to NOTIFIED so the watcher won't re-alert.
    """
    days_left = (subscription.trial_end_date - date.today()).days
    message = (
        f"Your free trial for **{subscription.service_name}** "
        f"expires in {days_left} day{'s' if days_left != 1 else ''}! "
        f"Cancel before {subscription.trial_end_date.strftime('%b %d, %Y')} "
        f"to avoid being charged"
        f"{f' ${subscription.cost_per_cycle}' if subscription.cost_per_cycle else ''}."
    )

    notif = Notification(
        user_id=user_id,
        subscription_id=subscription.id,
        notification_type=NotificationType.IN_APP,
        message=message,
    )
    db.add(notif)

    # Transition status
    subscription.status = TrialStatus.NOTIFIED
    db.commit()
    db.refresh(notif)
    logger.info("Alert created for user=%s sub=%s", user_id, subscription.service_name)
    return notif


def send_email_alert(
    user_email: str,
    subscription: Subscription,
) -> bool:
    """
    Send an email alert. Currently a stub; wire up SMTP in production.
    Returns True on success.
    """
    # TODO: integrate with SMTP via app.core.config SMTP settings
    logger.info(
        "EMAIL STUB: %s: trial for %s expires %s",
        user_email,
        subscription.service_name,
        subscription.trial_end_date,
    )
    return True


def get_user_notifications(
    db: Session,
    user_id: str,
    limit: int = 50,
) -> List[Notification]:
    """Fetch recent notifications for a user, newest first."""
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.sent_at.desc())
        .limit(limit)
        .all()
    )


def get_unread_count(db: Session, user_id: str) -> int:
    """Count notifications (used for badge display)."""
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .count()
    )

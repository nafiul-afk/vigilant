"""
Notification service for in-app and email alerts.
"""

from __future__ import annotations

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date
from typing import List

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.notification import Notification, NotificationType
from app.models.subscription import Subscription, TrialStatus

settings = get_settings()

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
    Send an email alert via SMTP.
    Returns True on success.
    """
    if not settings.SMTP_HOST or not settings.SMTP_USER:
        logger.warning("SMTP not configured. Skipping email alert for %s", user_email)
        return False

    try:
        days_left = (subscription.trial_end_date - date.today()).days
        
        # Message setup
        msg = MIMEMultipart()
        msg["From"] = settings.EMAIL_FROM
        msg["To"] = user_email
        msg["Subject"] = f"Action Required: {subscription.service_name} Trial Ending Soon"

        body = (
            f"Hello,\n\n"
            f"This is an automated alert from Vigilant.\n\n"
            f"Your free trial for {subscription.service_name} expires in {days_left} days "
            f"({subscription.trial_end_date.strftime('%b %d, %Y')}).\n"
            f"To avoid being charged ${subscription.cost_per_cycle or '0'}, please cancel "
            f"the trial if you no longer wish to continue.\n\n"
            f"Stay vigilant,\n"
            f"The Vigilant Team"
        )
        msg.attach(MIMEText(body, "plain"))

        # Connect and send
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.DEBUG:
                server.set_debuglevel(1)
            
            server.starttls() # Mailtrap supports STARTTLS
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)

        logger.info("Email alert sent to %s for %s", user_email, subscription.service_name)
        return True

    except Exception as e:
        logger.error("Failed to send email to %s: %s", user_email, e)
        return False


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


def send_welcome_email(user_email: str, username: str) -> bool:
    """Send a welcome email to a new user."""
    if not settings.SMTP_HOST or not settings.SMTP_USER:
        return False

    try:
        msg = MIMEMultipart()
        msg["From"] = settings.EMAIL_FROM
        msg["To"] = user_email
        msg["Subject"] = "Welcome to Vigilant!"

        body = (
            f"Hi {username},\n\n"
            f"Welcome to Vigilant! We're thrilled to help you track your subscriptions and trials.\n\n"
            f"With Vigilant, you'll never be caught off guard by a surprise renewal again. "
            f"Start by adding your first subscription at http://localhost:8000/dashboard\n\n"
            f"Stay vigilant,\n"
            f"The Vigilant Team"
        )
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)

        logger.info("Welcome email sent to %s", user_email)
        return True
    except Exception as e:
        logger.error("Failed to send welcome email to %s: %s", user_email, e)
        return False

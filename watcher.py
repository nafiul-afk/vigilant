#!/usr/bin/env python3
"""
Vigilant watcher process.
A standalone background process that polls the database for expiring
free trials and creates alerts.  Designed to run as a separate process
(e.g., via systemd, Docker sidecar, or a simple `python watcher.py`).

This NEVER blocks the main FastAPI thread.
"""

from __future__ import annotations

import logging
import signal
import sys
import time

from app.core.config import get_settings
from app.database.session import SessionLocal
from app.models.subscription import Subscription, TrialStatus
from app.services import notification_service, subscription_service

settings = get_settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | WATCHER | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("vigilant.watcher")

_running = True


def _handle_signal(signum, frame):
    global _running
    logger.info("Received signal %s; shutting down gracefully.", signum)
    _running = False


signal.signal(signal.SIGINT, _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)


def sweep() -> int:
    """
    Single sweep:
    1. Mark past-due subscriptions as EXPIRED.
    2. Find ACTIVE subs expiring within the alert window.
    3. Create in-app alerts and transition them to NOTIFIED.

    Returns the number of new alerts generated.
    """
    db = SessionLocal()
    alerts_created = 0
    try:
        # Phase 1: Expire overdue subscriptions
        expired_count = subscription_service.mark_expired(db)
        if expired_count:
            logger.info("Marked %d subscription(s) as EXPIRED.", expired_count)

        # Phase 2: Detect expiring subscriptions
        expiring = subscription_service.get_expiring_subscriptions(db)
        if not expiring:
            logger.debug("No expiring subscriptions found.")
            return 0

        logger.info("Found %d expiring subscription(s).", len(expiring))

        # Phase 3: Generate alerts
        for sub in expiring:
            # Transition to EXPIRING first (if still ACTIVE)
            if sub.status == TrialStatus.ACTIVE:
                sub.status = TrialStatus.EXPIRING
                db.commit()

            notification_service.create_in_app_alert(
                db=db,
                user_id=sub.owner_id,
                subscription=sub,
            )
            alerts_created += 1

            # Optional: send email too
            # owner = db.query(User).get(sub.owner_id)
            # notification_service.send_email_alert(owner.email, sub)

        logger.info("Created %d alert(s).", alerts_created)
    except Exception:
        logger.exception("Error during sweep; will retry next cycle.")
        db.rollback()
    finally:
        db.close()

    return alerts_created


def main():
    logger.info(
        "Vigilant watcher started; polling every %ds, alert window = %d days.",
        settings.WATCHER_POLL_INTERVAL,
        settings.WATCHER_ALERT_DAYS,
    )

    while _running:
        sweep()
        # Sleep in small increments so we can catch SIGTERM quickly
        for _ in range(settings.WATCHER_POLL_INTERVAL):
            if not _running:
                break
            time.sleep(1)

    logger.info("Watcher stopped.")


if __name__ == "__main__":
    main()

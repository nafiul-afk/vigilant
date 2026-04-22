"""
Vigilant — Notification Model
Tracks alert history so we don't spam users.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.database.session import Base


class NotificationType(str, enum.Enum):
    EMAIL = "email"
    IN_APP = "in_app"
    SMS = "sms"  # future


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subscription_id = Column(
        String(36),
        ForeignKey("subscriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    notification_type = Column(
        Enum(NotificationType),
        default=NotificationType.IN_APP,
        nullable=False,
    )
    message = Column(Text, nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="notifications")
    subscription = relationship("Subscription", back_populates="notifications")

    def __repr__(self) -> str:
        return f"<Notification {self.notification_type.value} → {self.user_id}>"

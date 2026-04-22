"""
Vigilant — Subscription Model
Tracks free trials and paid subscriptions the user wants to monitor.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database.session import Base


class TrialStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRING = "expiring"
    NOTIFIED = "notified"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        Index("ix_sub_trial_end", "trial_end_date"),
        Index("ix_sub_status", "status"),
        Index("ix_sub_owner_status", "owner_id", "status"),
    )

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    owner_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    service_name = Column(String(200), nullable=False)
    service_url = Column(String(512), nullable=True)
    cost_per_cycle = Column(Numeric(10, 2), nullable=True)
    billing_cycle = Column(String(50), nullable=True)  # monthly / yearly / etc.
    trial_start_date = Column(Date, nullable=False)
    trial_end_date = Column(Date, nullable=False)
    status = Column(
        Enum(TrialStatus),
        default=TrialStatus.ACTIVE,
        nullable=False,
    )
    notes = Column(Text, nullable=True)
    cancel_url = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    owner = relationship("User", back_populates="subscriptions")
    notifications = relationship(
        "Notification", back_populates="subscription", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Subscription {self.service_name} [{self.status.value}]>"

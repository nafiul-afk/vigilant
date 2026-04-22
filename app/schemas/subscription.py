"""
Vigilant — Subscription Schemas
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class SubscriptionCreate(BaseModel):
    service_name: str
    service_url: Optional[str] = None
    cost_per_cycle: Optional[float] = None
    billing_cycle: Optional[str] = "monthly"
    trial_start_date: date
    trial_end_date: date
    cancel_url: Optional[str] = None
    notes: Optional[str] = None


class SubscriptionUpdate(BaseModel):
    service_name: Optional[str] = None
    service_url: Optional[str] = None
    cost_per_cycle: Optional[float] = None
    billing_cycle: Optional[str] = None
    trial_end_date: Optional[date] = None
    cancel_url: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class SubscriptionOut(BaseModel):
    id: str
    service_name: str
    service_url: Optional[str]
    cost_per_cycle: Optional[float]
    billing_cycle: Optional[str]
    trial_start_date: date
    trial_end_date: date
    status: str
    cancel_url: Optional[str]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

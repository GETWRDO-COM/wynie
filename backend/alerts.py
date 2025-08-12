from __future__ import annotations
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class Alert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    symbol: str
    type: str  # 'price_above' | 'price_below' | 'pct_change_ge'
    value: float
    note: str | None = None
    enabled: bool = True
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    triggeredAt: datetime | None = None

class AlertCreate(BaseModel):
    symbol: str
    type: str
    value: float
    note: str | None = None

class Notification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    kind: str = "alert"
    symbol: str
    message: str
    createdAt: datetime = Field(default_factory=datetime.utcnow)
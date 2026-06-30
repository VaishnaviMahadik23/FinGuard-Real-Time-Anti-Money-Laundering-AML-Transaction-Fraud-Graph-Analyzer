"""
Alert ODM document model.
"""
from datetime import datetime
from typing import Optional
from beanie import Document, Indexed
from pydantic import Field
import uuid


class Alert(Document):
    alert_id: str = Field(default_factory=lambda: f"ALT-{uuid.uuid4().hex[:8].upper()}")
    tx_id: Indexed(str)
    account_id: Optional[str] = None
    severity: str  # critical | high | medium
    alert_type: str  # loop_detected | velocity_spike | structuring | layering | anomaly
    description: str
    risk_score: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved: bool = False
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    sar_filed: bool = False

    class Settings:
        name = "alerts"
        indexes = [
            [("created_at", -1)],
            [("severity", 1), ("resolved", 1)],
        ]

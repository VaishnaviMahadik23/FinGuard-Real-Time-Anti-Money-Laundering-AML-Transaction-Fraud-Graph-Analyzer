"""
Account ODM document model.
Stores polymorphic identity parameters and cached risk velocity matrices.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from beanie import Document, Indexed
from pydantic import Field
import uuid


class Account(Document):
    account_id: Indexed(str, unique=True) = Field(default_factory=lambda: f"ACC-{uuid.uuid4().hex[:6].upper()}")
    name: str
    country: str
    entity_type: str  # individual | corporate | shell
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Risk velocity matrix — cached and updated per transaction batch
    risk_velocity: Dict[str, Any] = Field(default_factory=lambda: {
        "tx_count_1h": 0,
        "tx_count_24h": 0,
        "volume_1h": 0.0,
        "volume_24h": 0.0,
        "unique_counterparties": 0,
        "avg_risk_score": 0.0,
        "max_risk_score": 0.0,
        "last_updated": None,
    })

    # Jurisdiction risk score (0-1)
    jurisdiction_risk: float = 0.0

    # AML flags
    is_frozen: bool = False
    is_pep: bool = False          # Politically Exposed Person
    is_sanctions: bool = False
    aml_flag_count: int = 0
    last_flagged_at: Optional[datetime] = None

    class Settings:
        name = "accounts"

"""
Transaction ODM document model.
"""
from datetime import datetime
from typing import Optional
from beanie import Document, Indexed
from pydantic import Field
import uuid


class Transaction(Document):
    tx_id: Indexed(str, unique=True) = Field(default_factory=lambda: f"TX{uuid.uuid4().hex[:8].upper()}")
    from_account_id: Indexed(str)
    to_account_id: Indexed(str)
    amount: float
    currency: str = "USD"
    tx_type: str  # WIRE | ACH | CRYPTO | SWIFT | INTERNAL | CASH
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # ML scores
    isolation_forest_score: float = 0.0
    autoencoder_error: float = 0.0
    risk_score: float = 0.0
    risk_level: str = "low"  # low | medium | high

    # Flags
    is_flagged: bool = False
    is_loop: bool = False
    pattern: Optional[str] = None  # smurfing | layering | loop | None
    is_frozen: bool = False
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None

    class Settings:
        name = "transactions"
        indexes = [
            [("timestamp", -1)],
            [("risk_score", -1)],
            [("from_account_id", 1), ("timestamp", -1)],
        ]

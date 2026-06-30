"""
Pydantic v2 schemas for API request/response validation.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ─── Transaction Schemas ─────────────────────────────────────────────────────

class TransactionCreate(BaseModel):
    from_account_id: str
    to_account_id: str
    amount: float = Field(gt=0)
    currency: str = "USD"
    tx_type: str = "WIRE"


class TransactionResponse(BaseModel):
    tx_id: str
    from_account_id: str
    to_account_id: str
    amount: float
    currency: str
    tx_type: str
    timestamp: datetime
    risk_score: float
    risk_level: str
    is_flagged: bool
    is_loop: bool
    pattern: Optional[str]
    isolation_forest_score: float
    autoencoder_error: float

    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    total: int
    items: List[TransactionResponse]


# ─── Account Schemas ─────────────────────────────────────────────────────────

class AccountCreate(BaseModel):
    name: str
    country: str
    entity_type: str = "individual"


class AccountResponse(BaseModel):
    account_id: str
    name: str
    country: str
    entity_type: str
    risk_velocity: dict
    jurisdiction_risk: float
    is_frozen: bool
    aml_flag_count: int

    model_config = {"from_attributes": True}


# ─── Alert Schemas ───────────────────────────────────────────────────────────

class AlertResponse(BaseModel):
    alert_id: str
    tx_id: str
    severity: str
    alert_type: str
    description: str
    risk_score: float
    created_at: datetime
    resolved: bool

    model_config = {"from_attributes": True}


# ─── Graph Schemas ───────────────────────────────────────────────────────────

class GraphNode(BaseModel):
    id: str
    label: str
    country: str
    entity_type: str
    risk_score: float
    tx_count: int
    is_flagged: bool
    is_frozen: bool


class GraphEdge(BaseModel):
    source: str
    target: str
    count: int
    total_volume: float
    is_suspicious: bool
    is_loop: bool


class GraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]


# ─── Analytics Schemas ───────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_transactions: int
    flagged_count: int
    high_risk_count: int
    suspicious_chains: int
    total_volume_usd: float
    avg_risk_score: float
    alerts_unresolved: int

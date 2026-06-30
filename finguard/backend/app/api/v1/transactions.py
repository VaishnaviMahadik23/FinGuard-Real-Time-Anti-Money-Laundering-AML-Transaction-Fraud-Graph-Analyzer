"""
Transaction endpoints — submit, query, flag, freeze.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from loguru import logger

from app.models.transaction import Transaction
from app.models.alert import Alert
from app.schemas.schemas import TransactionCreate, TransactionResponse, TransactionListResponse
from app.ml.risk_scorer import score_transaction
from app.api.websocket import broadcast_transaction

router = APIRouter()


@router.post("/", response_model=TransactionResponse, status_code=201)
async def submit_transaction(
    payload: TransactionCreate,
    background_tasks: BackgroundTasks,
):
    """
    Submit a transaction for real-time AML screening.
    Runs Isolation Forest + Autoencoder scoring and graph loop detection.
    """
    # Build scoring input
    tx_data = {
        "from_account_id": payload.from_account_id,
        "to_account_id": payload.to_account_id,
        "amount": payload.amount,
        "tx_type": payload.tx_type,
        # These would be enriched from Account lookup in production
        "from_country": "US",
        "to_country": "US",
        "from_type": "individual",
        "to_type": "individual",
    }

    scores = await score_transaction(tx_data)

    tx = Transaction(
        from_account_id=payload.from_account_id,
        to_account_id=payload.to_account_id,
        amount=payload.amount,
        currency=payload.currency,
        tx_type=payload.tx_type,
        **scores,
    )
    await tx.insert()
    logger.info(f"TX {tx.tx_id} scored: risk={scores['risk_score']:.3f} [{scores['risk_level']}]")

    # Fire alert in background if flagged
    if tx.is_flagged:
        background_tasks.add_task(_create_alert, tx)

    # Broadcast over WebSocket
    background_tasks.add_task(broadcast_transaction, tx)

    return tx


@router.get("/", response_model=TransactionListResponse)
async def list_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    risk_level: Optional[str] = None,
    flagged_only: bool = False,
):
    query = {}
    if risk_level:
        query["risk_level"] = risk_level
    if flagged_only:
        query["is_flagged"] = True

    total = await Transaction.find(query).count()
    items = await Transaction.find(query).sort("-timestamp").skip(skip).limit(limit).to_list()
    return {"total": total, "items": items}


@router.get("/flagged", response_model=TransactionListResponse)
async def get_flagged_transactions(limit: int = Query(100, le=500)):
    items = await Transaction.find({"is_flagged": True}).sort("-timestamp").limit(limit).to_list()
    return {"total": len(items), "items": items}


@router.get("/{tx_id}", response_model=TransactionResponse)
async def get_transaction(tx_id: str):
    tx = await Transaction.find_one({"tx_id": tx_id})
    if not tx:
        raise HTTPException(status_code=404, detail=f"Transaction {tx_id} not found")
    return tx


@router.post("/{tx_id}/freeze")
async def freeze_transaction(tx_id: str):
    tx = await Transaction.find_one({"tx_id": tx_id})
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    tx.is_frozen = True
    await tx.save()
    return {"status": "frozen", "tx_id": tx_id}


async def _create_alert(tx: Transaction):
    """Create an Alert document for a flagged transaction."""
    severity = "critical" if tx.risk_score > 0.85 else "high"
    alert_type = tx.pattern or "anomaly"
    alert = Alert(
        tx_id=tx.tx_id,
        account_id=tx.from_account_id,
        severity=severity,
        alert_type=alert_type,
        description=f"{'Loop chain detected' if tx.is_loop else 'Anomalous transaction'}: {tx.tx_id} "
                    f"(${tx.amount:,.0f} via {tx.tx_type}, score={tx.risk_score:.2f})",
        risk_score=tx.risk_score,
    )
    await alert.insert()

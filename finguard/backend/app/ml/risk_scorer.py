"""
Risk Scoring Service.
Combines Isolation Forest + Autoencoder scores into a final ensemble risk score,
then runs graph-based loop detection.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple

import numpy as np

from app.ml.model_registry import ModelRegistry
from app.core.config import settings
from app.db.client import get_db


# Ensemble weights
IF_WEIGHT = 0.55
AE_WEIGHT = 0.45


async def score_transaction(tx_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Full scoring pipeline:
    1. Build feature vector
    2. Isolation Forest anomaly score
    3. Autoencoder reconstruction error
    4. Weighted ensemble
    5. Graph loop detection
    6. Risk level classification
    """
    # Enrich with velocity features from MongoDB
    enriched = await _enrich_with_velocity(tx_data)

    # 1. Isolation Forest
    if_model = ModelRegistry.get_if()
    if_score = if_model.score(enriched)

    # 2. Autoencoder
    ae_model = ModelRegistry.get_ae()
    threshold = ModelRegistry.get_ae_threshold()
    features = if_model._extract_features(enriched)
    ae_score = ae_model.anomaly_score(features.flatten(), threshold)
    ae_error = ae_model.reconstruction_error(features.flatten())

    # 3. Ensemble
    ensemble_score = (IF_WEIGHT * if_score) + (AE_WEIGHT * ae_score)
    ensemble_score = float(np.clip(ensemble_score, 0.0, 0.99))

    # 4. Loop detection
    is_loop = await _detect_loop(tx_data["from_account_id"], tx_data["to_account_id"])
    if is_loop:
        ensemble_score = min(ensemble_score + 0.25, 0.99)

    # 5. Classify
    risk_level = _classify_risk(ensemble_score)
    is_flagged = ensemble_score >= settings.RISK_HIGH_THRESHOLD or is_loop

    return {
        "isolation_forest_score": round(if_score, 4),
        "autoencoder_error": round(ae_error, 4),
        "risk_score": round(ensemble_score, 4),
        "risk_level": risk_level,
        "is_flagged": is_flagged,
        "is_loop": is_loop,
        "pattern": _detect_pattern(tx_data, ensemble_score, is_loop),
    }


def _classify_risk(score: float) -> str:
    if score >= settings.RISK_HIGH_THRESHOLD:
        return "high"
    elif score >= settings.RISK_MEDIUM_THRESHOLD:
        return "medium"
    return "low"


def _detect_pattern(tx_data: Dict, score: float, is_loop: bool) -> str | None:
    amount = tx_data.get("amount", 0)
    # Structuring / smurfing: just below $10k CTR threshold
    if 8_500 <= amount <= 9_999:
        return "smurfing"
    # Layering: through shell company
    if tx_data.get("to_type") == "shell" and score > 0.5:
        return "layering"
    if is_loop:
        return "loop"
    if score > 0.65:
        return "anomaly"
    return None


async def _enrich_with_velocity(tx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Add 1h velocity and volume from MongoDB."""
    try:
        db = get_db()
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        pipe = [
            {"$match": {
                "from_account_id": tx_data["from_account_id"],
                "timestamp": {"$gte": one_hour_ago}
            }},
            {"$group": {
                "_id": None,
                "count": {"$sum": 1},
                "volume": {"$sum": "$amount"},
                "unique_dst": {"$addToSet": "$to_account_id"}
            }}
        ]
        result = await db["transactions"].aggregate(pipe).to_list(1)
        if result:
            tx_data["velocity_1h"] = result[0]["count"]
            tx_data["volume_1h"] = result[0]["volume"]
            tx_data["unique_counterparties_7d"] = len(result[0]["unique_dst"])
    except Exception:
        pass  # Gracefully degrade if DB unavailable
    return tx_data


async def _detect_loop(from_id: str, to_id: str, max_depth: int = 5) -> bool:
    """
    BFS loop detection using MongoDB graph lookup.
    Checks if to_id can reach from_id within max_depth hops.
    """
    try:
        db = get_db()
        pipeline = [
            {"$match": {"from_account_id": to_id}},
            {"$graphLookup": {
                "from": "transactions",
                "startWith": "$to_account_id",
                "connectFromField": "to_account_id",
                "connectToField": "from_account_id",
                "as": "chain",
                "maxDepth": max_depth - 1,
                "depthField": "depth"
            }},
            {"$project": {"chain.to_account_id": 1}},
            {"$limit": 1}
        ]
        results = await db["transactions"].aggregate(pipeline).to_list(1)
        if results:
            chain_ids = [c["to_account_id"] for c in results[0].get("chain", [])]
            return from_id in chain_ids
    except Exception:
        pass
    return False

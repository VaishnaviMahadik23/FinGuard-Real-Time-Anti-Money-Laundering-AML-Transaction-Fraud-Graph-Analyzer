"""
tests/backend/test_risk_scorer.py
Unit tests for the ML scoring pipeline.
"""
import pytest
import numpy as np


def test_isolation_forest_heuristic():
    """IF heuristic fallback scores shell-company txs higher."""
    from app.ml.isolation_forest import AMLIsolationForest
    model = AMLIsolationForest()

    normal_tx = {
        "from_account_id": "ACC-001", "to_account_id": "ACC-004",
        "amount": 500, "from_country": "US", "to_country": "US",
        "from_type": "individual", "to_type": "individual",
        "tx_type": "ACH", "velocity_1h": 1, "volume_1h": 500,
        "unique_counterparties_7d": 2,
    }
    risky_tx = {
        **normal_tx,
        "from_country": "BVI", "to_country": "PAN",
        "from_type": "shell", "to_type": "shell",
        "amount": 450_000,
    }
    normal_score = model.score(normal_tx)
    risky_score  = model.score(risky_tx)
    assert risky_score > normal_score
    assert 0.0 <= normal_score <= 1.0
    assert 0.0 <= risky_score  <= 1.0


def test_autoencoder_reconstruction():
    """Autoencoder returns a non-negative reconstruction error."""
    from app.ml.autoencoder import TransactionAutoencoder
    ae = TransactionAutoencoder(input_dim=16)
    ae.eval()
    features = np.random.rand(16).astype(np.float32)
    error = ae.reconstruction_error(features)
    assert error >= 0.0


def test_pattern_detection():
    """Pattern detector correctly identifies smurfing amounts."""
    from app.ml.risk_scorer import _detect_pattern
    tx = {"amount": 9_500, "to_type": "individual"}
    assert _detect_pattern(tx, 0.3, False) == "smurfing"

    tx2 = {"amount": 200_000, "to_type": "shell"}
    assert _detect_pattern(tx2, 0.6, False) == "layering"

    tx3 = {"amount": 5_000, "to_type": "individual"}
    assert _detect_pattern(tx3, 0.2, True) == "loop"

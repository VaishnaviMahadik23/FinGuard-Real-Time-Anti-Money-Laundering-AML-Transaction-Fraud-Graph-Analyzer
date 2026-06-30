"""
Isolation Forest wrapper for AML anomaly detection.
Wraps scikit-learn's IsolationForest with domain-specific feature engineering.
"""
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from typing import Dict, Any


# High-risk jurisdiction codes (FATF grey/black list approximation)
HIGH_RISK_JURISDICTIONS = {
    "BVI", "PAN", "KY", "VG", "AI", "TC",  # Offshore
    "IR", "KP", "SY", "YE", "LY",           # Sanctions
    "RU", "BY", "MM",                         # Elevated risk
}

MEDIUM_RISK_JURISDICTIONS = {
    "AE", "SA", "TR", "VE", "ZW", "NI", "HT",
    "PH", "PK", "LB", "JO",
}


class AMLIsolationForest:
    def __init__(self, contamination: float = 0.08, n_estimators: int = 200):
        self.model = IsolationForest(
            contamination=contamination,
            n_estimators=n_estimators,
            random_state=42,
            max_samples="auto",
        )
        self.scaler = StandardScaler()
        self._is_trained = False

    def _extract_features(self, tx_data: Dict[str, Any]) -> np.ndarray:
        """
        Extract 16-dimensional feature vector from a transaction dict.
        Fields: amount, log_amount, jurisdiction_risk_src, jurisdiction_risk_dst,
                is_shell_src, is_shell_dst, hour_of_day, is_round_amount,
                velocity_1h, volume_1h, unique_cp_7d, amount_zscore,
                cross_border, pep_involved, tx_type_encoded, weekend
        """
        src_country = tx_data.get("from_country", "US")
        dst_country = tx_data.get("to_country", "US")

        j_src = 1.0 if src_country in HIGH_RISK_JURISDICTIONS else (
            0.5 if src_country in MEDIUM_RISK_JURISDICTIONS else 0.0)
        j_dst = 1.0 if dst_country in HIGH_RISK_JURISDICTIONS else (
            0.5 if dst_country in MEDIUM_RISK_JURISDICTIONS else 0.0)

        amount = float(tx_data.get("amount", 0))
        hour = tx_data.get("hour", 12)
        velocity = float(tx_data.get("velocity_1h", 0))
        volume_1h = float(tx_data.get("volume_1h", 0))
        unique_cp = float(tx_data.get("unique_counterparties_7d", 0))

        tx_type_map = {"WIRE": 0, "ACH": 1, "CRYPTO": 2, "SWIFT": 3, "INTERNAL": 4, "CASH": 5}
        tx_type_enc = tx_type_map.get(tx_data.get("tx_type", "WIRE"), 0) / 5.0

        features = np.array([
            np.log1p(amount) / 15.0,                    # log-scaled amount
            amount / 1_000_000,                           # raw amount normalised
            j_src,                                        # source jurisdiction risk
            j_dst,                                        # dest jurisdiction risk
            1.0 if tx_data.get("from_type") == "shell" else 0.0,
            1.0 if tx_data.get("to_type") == "shell" else 0.0,
            hour / 23.0,                                  # time of day
            1.0 if amount % 10_000 == 0 else 0.0,       # round-number flag
            min(velocity / 20.0, 1.0),                   # velocity (capped)
            np.log1p(volume_1h) / 18.0,                 # 1h volume
            min(unique_cp / 50.0, 1.0),                  # counterparty diversity
            min(amount / 9_999, 1.0) if amount < 10_000 else 0.0,  # structuring
            1.0 if src_country != dst_country else 0.0,  # cross-border
            1.0 if tx_data.get("is_pep", False) else 0.0,
            tx_type_enc,
            1.0 if tx_data.get("is_weekend", False) else 0.0,
        ], dtype=np.float32)

        return features.reshape(1, -1)

    def fit(self, transactions: list):
        X = np.vstack([self._extract_features(t) for t in transactions])
        self.scaler.fit(X)
        X_scaled = self.scaler.transform(X)
        self.model.fit(X_scaled)
        self._is_trained = True

    def score(self, tx_data: Dict[str, Any]) -> float:
        """
        Returns anomaly score in [0, 1] where 1 = most anomalous.
        Maps sklearn's score_samples output (negative = more anomalous) to [0,1].
        """
        features = self._extract_features(tx_data)
        if self._is_trained:
            features_scaled = self.scaler.transform(features)
            raw = self.model.score_samples(features_scaled)[0]
            # sklearn returns values roughly in [-0.7, 0.1]; map to [0,1]
            score = np.clip((raw + 0.7) / 0.8, 0, 1)
            score = 1.0 - score  # invert: high = anomalous
        else:
            # Heuristic fallback when not trained
            score = self._heuristic_score(tx_data)
        return float(np.clip(score, 0.0, 1.0))

    def _heuristic_score(self, tx_data: Dict[str, Any]) -> float:
        """Rule-based fallback before first training."""
        score = 0.0
        amount = float(tx_data.get("amount", 0))
        if amount > 50_000: score += 0.2
        if amount > 200_000: score += 0.2
        src = tx_data.get("from_country", "US")
        dst = tx_data.get("to_country", "US")
        if src in HIGH_RISK_JURISDICTIONS or dst in HIGH_RISK_JURISDICTIONS:
            score += 0.25
        if tx_data.get("from_type") == "shell" or tx_data.get("to_type") == "shell":
            score += 0.25
        if tx_data.get("velocity_1h", 0) > 5:
            score += 0.1
        return min(score, 0.95)

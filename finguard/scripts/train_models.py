"""
scripts/train_models.py
Trains the Isolation Forest and Autoencoder on synthetic transaction data,
then saves models to the ml_models/ directory.

Run: python scripts/train_models.py
"""
"""
scripts/train_models.py
"""
import sys, os

# ✅ MUST be before any app.* imports
BACKEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
sys.path.insert(0, BACKEND_DIR)

import numpy as np
import torch
import joblib
from pathlib import Path
from app.ml.isolation_forest import AMLIsolationForest
from app.ml.autoencoder import TransactionAutoencoder, AutoencoderTrainer
from app.core.config import settings

# ... rest of your file unchanged

MODEL_DIR = Path(settings.MODEL_DIR)
MODEL_DIR.mkdir(parents=True, exist_ok=True)

COUNTRIES = ["US", "UK", "DE", "SG", "JP", "AU", "CA", "FR", "NO", "HK"]
HIGH_RISK  = ["BVI", "PAN", "KY", "RU", "AE", "IR"]
TX_TYPES   = ["WIRE", "ACH", "CRYPTO", "SWIFT", "INTERNAL", "CASH"]

def generate_synthetic_data(n: int = 100_000):
    """Generate synthetic normal transaction feature vectors (16-dim)."""
    rng = np.random.default_rng(42)

    # Normal transactions
    normal_count = int(n * 0.92)
    anomaly_count = n - normal_count

    def normal_tx(count):
        return {
            "from_country": rng.choice(COUNTRIES, count),
            "to_country":   rng.choice(COUNTRIES, count),
            "from_type":    rng.choice(["individual", "corporate"], count, p=[0.6, 0.4]),
            "to_type":      rng.choice(["individual", "corporate"], count, p=[0.6, 0.4]),
            "amount":       rng.exponential(5000, count),
            "hour":         rng.integers(8, 18, count),
            "velocity_1h":  rng.poisson(1.5, count),
            "volume_1h":    rng.exponential(10000, count),
            "unique_cp_7d": rng.poisson(3, count),
            "tx_type":      rng.choice(TX_TYPES, count),
        }

    def anomaly_tx(count):
        return {
            "from_country": rng.choice(HIGH_RISK, count),
            "to_country":   rng.choice(HIGH_RISK + COUNTRIES, count),
            "from_type":    rng.choice(["shell", "individual"], count, p=[0.7, 0.3]),
            "to_type":      rng.choice(["shell", "corporate"], count, p=[0.6, 0.4]),
            "amount":       rng.uniform(8500, 500000, count),
            "hour":         rng.choice([2, 3, 22, 23], count),
            "velocity_1h":  rng.integers(8, 25, count),
            "volume_1h":    rng.uniform(50000, 2000000, count),
            "unique_cp_7d": rng.integers(10, 50, count),
            "tx_type":      rng.choice(["CRYPTO", "WIRE", "SWIFT"], count),
        }

    model = AMLIsolationForest()

    all_tx = []
    nd = normal_tx(normal_count)
    for i in range(normal_count):
        all_tx.append({k: (v[i].item() if hasattr(v[i], 'item') else v[i]) for k, v in nd.items()})

    ad = anomaly_tx(anomaly_count)
    for i in range(anomaly_count):
        all_tx.append({k: (v[i].item() if hasattr(v[i], 'item') else v[i]) for k, v in ad.items()})

    # Extract feature matrix
    X = np.vstack([model._extract_features(t) for t in all_tx])
    return X, model


def train_isolation_forest(X: np.ndarray) -> AMLIsolationForest:
    print(f"\n[1/2] Training Isolation Forest on {len(X):,} samples...")
    model = AMLIsolationForest(contamination=settings.ISOLATION_FOREST_CONTAMINATION)
    # Fit scaler then model
    from sklearn.preprocessing import StandardScaler
    model.scaler.fit(X)
    X_scaled = model.scaler.transform(X)
    model.model.fit(X_scaled)
    model._is_trained = True

    out_path = MODEL_DIR / "isolation_forest.pkl"
    joblib.dump(model, out_path)
    print(f"    ✓ Saved to {out_path}")
    return model


def train_autoencoder(X: np.ndarray):
    print(f"\n[2/2] Training Autoencoder on {len(X):,} samples (50 epochs)...")
    # Normalise to [0,1] for sigmoid output
    X_norm = X.copy()
    X_norm = np.clip(X_norm, 0, 1)

    ae = TransactionAutoencoder(input_dim=16)
    trainer = AutoencoderTrainer(ae, lr=1e-3)
    history = trainer.fit(X_norm, epochs=50, batch_size=512)

    out_path = MODEL_DIR / "autoencoder.pt"
    torch.save(ae.state_dict(), out_path)
    final_loss = history[-1]
    print(f"    ✓ Final loss: {final_loss:.6f}")
    print(f"    ✓ Saved to {out_path}")


if __name__ == "__main__":
    print("=" * 50)
    print("  FinGuard — Model Training Pipeline")
    print("=" * 50)

    X, _ = generate_synthetic_data(100_000)
    print(f"  Feature matrix: {X.shape}")

    train_isolation_forest(X)
    train_autoencoder(X)

    print("\n✅ All models trained and saved to", MODEL_DIR)

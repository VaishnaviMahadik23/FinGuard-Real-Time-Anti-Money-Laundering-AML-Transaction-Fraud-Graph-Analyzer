"""
Model Registry — manages Isolation Forest + Autoencoder lifecycle.
Models are loaded once at startup and reused across all requests.
"""
import os
import joblib
import torch
from loguru import logger
from pathlib import Path

from app.core.config import settings
from app.ml.isolation_forest import AMLIsolationForest
from app.ml.autoencoder import TransactionAutoencoder


class ModelRegistry:
    _if_model: AMLIsolationForest | None = None
    _ae_model: TransactionAutoencoder | None = None
    _ae_threshold: float = settings.AUTOENCODER_THRESHOLD

    @classmethod
    async def load(cls):
        model_dir = Path(settings.MODEL_DIR)
        model_dir.mkdir(parents=True, exist_ok=True)

        if_path = model_dir / "isolation_forest.pkl"
        ae_path = model_dir / "autoencoder.pt"

        # Load or create Isolation Forest
        if if_path.exists():
            cls._if_model = joblib.load(if_path)
            logger.info(f"Isolation Forest loaded from {if_path}")
        else:
            logger.warning("No pre-trained IF model found — initialising untrained model")
            cls._if_model = AMLIsolationForest(
                contamination=settings.ISOLATION_FOREST_CONTAMINATION
            )

        # Load or create Autoencoder
        if ae_path.exists():
            cls._ae_model = TransactionAutoencoder(input_dim=16)
            cls._ae_model.load_state_dict(torch.load(ae_path, map_location="cpu"))
            cls._ae_model.eval()
            logger.info(f"Autoencoder loaded from {ae_path}")
        else:
            logger.warning("No pre-trained AE model found — initialising untrained model")
            cls._ae_model = TransactionAutoencoder(input_dim=16)
            cls._ae_model.eval()

    @classmethod
    def get_if(cls) -> AMLIsolationForest:
        if cls._if_model is None:
            raise RuntimeError("Isolation Forest model not loaded")
        return cls._if_model

    @classmethod
    def get_ae(cls) -> TransactionAutoencoder:
        if cls._ae_model is None:
            raise RuntimeError("Autoencoder model not loaded")
        return cls._ae_model

    @classmethod
    def get_ae_threshold(cls) -> float:
        return cls._ae_threshold

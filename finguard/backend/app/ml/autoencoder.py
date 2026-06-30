"""
Autoencoder Neural Network — PyTorch implementation.
Learns compressed representation of normal transaction behaviour.
High reconstruction error → anomalous transaction.

Architecture: 128 → 64 → 32 → 16 → 32 → 64 → 128
"""
import torch
import torch.nn as nn
import numpy as np
from typing import Tuple


class TransactionAutoencoder(nn.Module):
    """
    Symmetric autoencoder with bottleneck dimension of 16.
    Trained to reconstruct normal transaction feature vectors;
    anomalous transactions yield high MSE reconstruction error.
    """

    def __init__(self, input_dim: int = 16):
        super().__init__()
        self.input_dim = input_dim

        # Encoder: compress input to latent space
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.BatchNorm1d(128),
            nn.LeakyReLU(0.2),
            nn.Dropout(0.1),

            nn.Linear(128, 64),
            nn.BatchNorm1d(64),
            nn.LeakyReLU(0.2),
            nn.Dropout(0.1),

            nn.Linear(64, 32),
            nn.BatchNorm1d(32),
            nn.LeakyReLU(0.2),

            nn.Linear(32, 16),   # bottleneck
            nn.Sigmoid(),
        )

        # Decoder: reconstruct from latent space
        self.decoder = nn.Sequential(
            nn.Linear(16, 32),
            nn.LeakyReLU(0.2),

            nn.Linear(32, 64),
            nn.LeakyReLU(0.2),
            nn.Dropout(0.1),

            nn.Linear(64, 128),
            nn.BatchNorm1d(128),
            nn.LeakyReLU(0.2),
            nn.Dropout(0.1),

            nn.Linear(128, input_dim),
            nn.Sigmoid(),          # features normalised to [0,1]
        )

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        latent = self.encoder(x)
        reconstructed = self.decoder(latent)
        return reconstructed, latent

    @torch.no_grad()
    def reconstruction_error(self, features: np.ndarray) -> float:
        """
        Compute per-sample MSE reconstruction error.
        Returns a scalar in [0, ∞); threshold is typically ~0.42.
        """
        self.eval()
        x = torch.tensor(features, dtype=torch.float32)
        if x.dim() == 1:
            x = x.unsqueeze(0)
        recon, _ = self.forward(x)
        error = nn.functional.mse_loss(recon, x, reduction="mean")
        return float(error.item())

    @torch.no_grad()
    def anomaly_score(self, features: np.ndarray, threshold: float = 0.42) -> float:
        """
        Normalise reconstruction error to [0,1] relative to threshold.
        score > 1.0 → anomalous; clipped to [0,1] for combining with IF.
        """
        err = self.reconstruction_error(features)
        return float(np.clip(err / threshold, 0.0, 1.0))


class AutoencoderTrainer:
    """Wrapper to train the autoencoder on normal transaction batches."""

    def __init__(self, model: TransactionAutoencoder, lr: float = 1e-3):
        self.model = model
        self.optimizer = torch.optim.Adam(model.parameters(), lr=lr)
        self.criterion = nn.MSELoss()

    def train_epoch(self, X: np.ndarray, batch_size: int = 256) -> float:
        self.model.train()
        X_t = torch.tensor(X, dtype=torch.float32)
        losses = []
        for i in range(0, len(X_t), batch_size):
            batch = X_t[i:i + batch_size]
            self.optimizer.zero_grad()
            recon, _ = self.model(batch)
            loss = self.criterion(recon, batch)
            loss.backward()
            self.optimizer.step()
            losses.append(loss.item())
        return float(np.mean(losses))

    def fit(self, X: np.ndarray, epochs: int = 50, batch_size: int = 256) -> list:
        history = []
        for epoch in range(epochs):
            loss = self.train_epoch(X, batch_size)
            history.append(loss)
            if (epoch + 1) % 10 == 0:
                print(f"  Epoch {epoch+1}/{epochs} — loss: {loss:.6f}")
        return history

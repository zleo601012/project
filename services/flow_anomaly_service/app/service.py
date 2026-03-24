from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import torch

from .config import settings
from .model import LSTMAutoencoder


class FlowAnomalyDetector:
    """Encapsulates model/scaler/threshold loading and inference."""

    def __init__(self) -> None:
        self.device = torch.device("cpu")
        self.model: LSTMAutoencoder | None = None
        self.scaler: Any | None = None
        self.threshold: float | None = None

    def load(self) -> None:
        required = [settings.model_path, settings.scaler_path, settings.threshold_path]
        missing = [str(path) for path in required if not Path(path).exists()]
        if missing:
            raise FileNotFoundError(
                "Missing required artifacts. Please run training first. Missing: " + ", ".join(missing)
            )

        self.model = LSTMAutoencoder(
            input_size=len(settings.feature_names),
            hidden_size=settings.hidden_size,
            latent_size=settings.latent_size,
            num_layers=settings.num_layers,
            dropout=settings.dropout,
        )
        state_dict = torch.load(settings.model_path, map_location=self.device)
        self.model.load_state_dict(state_dict)
        self.model.to(self.device)
        self.model.eval()

        self.scaler = joblib.load(settings.scaler_path)
        with Path(settings.threshold_path).open("r", encoding="utf-8") as f:
            threshold_obj = json.load(f)
        self.threshold = float(threshold_obj["threshold"])

    @torch.no_grad()
    def detect(self, window: list[dict[str, float]]) -> dict[str, float | bool | int | str]:
        if self.model is None or self.scaler is None or self.threshold is None:
            raise RuntimeError("Detector is not initialized. Call load() first.")

        values = np.array(
            [[point[name] for name in settings.feature_names] for point in window],
            dtype=np.float32,
        )

        scaled = self.scaler.transform(values)
        x = torch.tensor(scaled, dtype=torch.float32, device=self.device).unsqueeze(0)
        reconstruction = self.model(x)
        mse = torch.mean((x - reconstruction) ** 2).item()

        return {
            "is_anomaly": bool(mse > self.threshold),
            "anomaly_score": float(mse),
            "threshold": float(self.threshold),
            "reconstruction_error": float(mse),
            "model_name": settings.model_name,
            "window_length": settings.window_length,
        }

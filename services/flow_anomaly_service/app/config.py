from __future__ import annotations

import os
from pathlib import Path


class Settings:
    """Runtime settings for inference service."""

    model_name: str = "lstm_autoencoder"
    window_length: int = int(os.getenv("WINDOW_LENGTH", "12"))
    feature_names: tuple[str, ...] = ("flow_m3s", "rain_intensity_mmph", "temp_C")
    hidden_size: int = int(os.getenv("HIDDEN_SIZE", "128"))
    latent_size: int = int(os.getenv("LATENT_SIZE", "64"))
    num_layers: int = int(os.getenv("NUM_LAYERS", "2"))
    dropout: float = float(os.getenv("DROPOUT", "0.2"))

    model_path: Path = Path(os.getenv("MODEL_PATH", "artifacts/model.pt"))
    scaler_path: Path = Path(os.getenv("SCALER_PATH", "artifacts/scaler.pkl"))
    threshold_path: Path = Path(os.getenv("THRESHOLD_PATH", "artifacts/threshold.json"))


settings = Settings()

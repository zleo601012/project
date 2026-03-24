from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch
from sklearn.preprocessing import StandardScaler
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from app.config import settings
from app.model import LSTMAutoencoder


def generate_mock_data(rows: int = 1200, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    t = np.arange(rows)
    flow = 2.0 + 0.4 * np.sin(2 * np.pi * t / 48) + rng.normal(0, 0.05, rows)
    rain = np.maximum(0.0, rng.gamma(1.2, 0.6, rows) - 0.4)
    temp = 20.0 + 4.0 * np.sin(2 * np.pi * t / 144) + rng.normal(0, 0.2, rows)
    return pd.DataFrame(
        {
            "flow_m3s": flow,
            "rain_intensity_mmph": rain,
            "temp_C": temp,
        }
    )


def build_windows(data: np.ndarray, window_length: int) -> np.ndarray:
    if len(data) < window_length:
        raise ValueError(f"Not enough data points: need >= {window_length}, got {len(data)}")
    return np.stack([data[i : i + window_length] for i in range(0, len(data) - window_length + 1)])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train LSTM autoencoder for flow anomaly detection")
    parser.add_argument("--train-csv", type=str, default=None, help="Path to CSV for normal samples")
    parser.add_argument("--output-dir", type=str, default="artifacts")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--threshold-quantile", type=float, default=0.95)
    parser.add_argument("--use-mock-data", action="store_true")
    parser.add_argument("--mock-rows", type=int, default=1200)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.train_csv:
        df = pd.read_csv(args.train_csv)
    elif args.use_mock_data:
        df = generate_mock_data(rows=args.mock_rows)
    else:
        raise ValueError("Please provide --train-csv or use --use-mock-data")

    missing_cols = [c for c in settings.feature_names if c not in df.columns]
    if missing_cols:
        raise ValueError(f"CSV missing required columns: {missing_cols}")

    raw = df[list(settings.feature_names)].astype(np.float32).values
    scaler = StandardScaler()
    scaled = scaler.fit_transform(raw)

    windows = build_windows(scaled, settings.window_length)
    tensor_data = torch.tensor(windows, dtype=torch.float32)
    dataloader = DataLoader(TensorDataset(tensor_data), batch_size=args.batch_size, shuffle=True)

    model = LSTMAutoencoder(
        input_size=len(settings.feature_names),
        hidden_size=settings.hidden_size,
        latent_size=settings.latent_size,
        num_layers=settings.num_layers,
        dropout=settings.dropout,
    )
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    criterion = nn.MSELoss()

    model.train()
    for epoch in range(args.epochs):
        epoch_loss = 0.0
        for (batch_x,) in dataloader:
            optimizer.zero_grad()
            recon = model(batch_x)
            loss = criterion(recon, batch_x)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item() * batch_x.shape[0]
        avg_loss = epoch_loss / len(tensor_data)
        print(f"epoch={epoch + 1}/{args.epochs}, loss={avg_loss:.6f}")

    model.eval()
    with torch.no_grad():
        recon = model(tensor_data)
        per_window_mse = torch.mean((tensor_data - recon) ** 2, dim=(1, 2)).numpy()

    threshold = float(np.quantile(per_window_mse, args.threshold_quantile))

    torch.save(model.state_dict(), output_dir / "model.pt")
    joblib.dump(scaler, output_dir / "scaler.pkl")
    with (output_dir / "threshold.json").open("w", encoding="utf-8") as f:
        json.dump(
            {
                "threshold": threshold,
                "quantile": args.threshold_quantile,
                "mean_reconstruction_error": float(np.mean(per_window_mse)),
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"Saved model to: {output_dir / 'model.pt'}")
    print(f"Saved scaler to: {output_dir / 'scaler.pkl'}")
    print(f"Saved threshold to: {output_dir / 'threshold.json'}")


if __name__ == "__main__":
    main()

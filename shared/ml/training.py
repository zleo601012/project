from __future__ import annotations

from importlib import import_module
from pathlib import Path


def train_service(service_name: str, dataset_path: str | Path, limit: int | None = None) -> dict:
    module = import_module(f'services.{service_name}.logic')
    return module.train(str(dataset_path), limit=limit)

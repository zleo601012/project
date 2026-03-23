from __future__ import annotations

import json
from pathlib import Path
import joblib
from shared.config.settings import get_settings


def model_path(service_name: str) -> Path:
    return get_settings().models_dir / f'{service_name}.joblib'


def metadata_path(service_name: str) -> Path:
    return get_settings().models_dir / f'{service_name}.metadata.json'


def save_model(service_name: str, model, metadata: dict) -> None:
    path = model_path(service_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
    metadata_path(service_name).write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding='utf-8')


def load_model(service_name: str):
    return joblib.load(model_path(service_name))


def load_metadata(service_name: str) -> dict:
    return json.loads(metadata_path(service_name).read_text(encoding='utf-8'))

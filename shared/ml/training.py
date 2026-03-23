from __future__ import annotations

from pathlib import Path
from shared.config.service_catalog import SERVICE_CATALOG
from shared.ml.feature_engineering import make_feature_vector
from shared.ml.model_io import save_model
from shared.schemas.common import BuildTasksRequest
from shared.utils.dataset import load_records
from shared.utils.windowing import build_tasks
from sklearn.ensemble import IsolationForest
from lightgbm import LGBMRegressor
from xgboost import XGBClassifier


def _build_tasks(service_name: str, dataset_path: str | Path, limit: int | None = None):
    records = load_records(dataset_path, limit=limit)
    return build_tasks(BuildTasksRequest(
        records=records,
        source_edge_node='trainer',
        target_services=[service_name],
        deadline_ms=3000,
    )).generated_tasks


def _last_value(task, field: str) -> float:
    return float(getattr(task.features, field)[-1])


def _delta_value(task, field: str) -> float:
    values = [float(v) for v in getattr(task.features, field)]
    return values[-1] - values[0]


def _weak_score(task, fields: list[str]) -> float:
    parts = []
    for field in fields:
        parts.append(abs(_last_value(task, field)))
        parts.append(abs(_delta_value(task, field)))
    return sum(parts) / max(len(parts), 1)


def _threshold(scores: list[float], percentile: float) -> float:
    ordered = sorted(scores)
    index = max(int(percentile * len(ordered)) - 1, 0)
    return ordered[index]


def train_service(service_name: str, dataset_path: str | Path, limit: int | None = None) -> dict:
    definition = SERVICE_CATALOG[service_name]
    tasks = _build_tasks(service_name, dataset_path, limit=limit)
    vectors = [make_feature_vector(task) for task in tasks]
    metadata = {
        'service_name': service_name,
        'model_name': definition.model_name,
        'model_version': definition.model_version,
        'training_samples': len(vectors),
        'dataset_path': str(dataset_path),
        'window_length': definition.window_length,
        'task_type': definition.task_type,
    }

    if definition.model_name == 'IsolationForest':
        model = IsolationForest(random_state=42, contamination=0.1)
        model.fit(vectors)
        scores = [-float(score) for score in model.score_samples(vectors)]
        metadata['threshold'] = _threshold(scores, 0.9)
    elif definition.task_type == 'forecast':
        usable_tasks = tasks[:-1]
        future_tasks = tasks[1:]
        target_field = definition.target_field or definition.input_fields[0]
        features = [make_feature_vector(task) for task in usable_tasks]
        targets = [_last_value(task, target_field) for task in future_tasks]
        usable = min(len(features), len(targets))
        features = features[:usable]
        targets = targets[:usable]
        model = LGBMRegressor(random_state=42, n_estimators=50, learning_rate=0.1, max_depth=4)
        model.fit(features, targets)
        metadata['training_samples'] = len(features)
        metadata['target_field'] = target_field
    else:
        weak_fields = definition.weak_label_fields or definition.input_fields[:1]
        weak_scores = [_weak_score(task, weak_fields) for task in tasks]
        positive_threshold = _threshold(weak_scores, 0.8)
        labels = [1 if score >= positive_threshold else 0 for score in weak_scores]
        model = XGBClassifier(random_state=42)
        model.fit(vectors, labels)
        metadata['threshold'] = 0.5
        metadata['weak_label_threshold'] = positive_threshold
        metadata['positive_ratio'] = sum(labels) / max(len(labels), 1)

    save_model(service_name, model, metadata)
    return metadata

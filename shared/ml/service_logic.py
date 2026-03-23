from __future__ import annotations

from pathlib import Path

from lightgbm import LGBMRegressor
from shared.config.service_definition import ServiceDefinition
from shared.ml.feature_engineering import make_feature_vector
from shared.ml.model_io import save_model
from shared.schemas.common import BuildTasksRequest
from shared.utils.dataset import load_records
from shared.utils.windowing import build_tasks
from sklearn.ensemble import IsolationForest
from xgboost import XGBClassifier


def build_training_tasks(definition: ServiceDefinition, dataset_path: str | Path, limit: int | None = None):
    records = load_records(dataset_path, limit=limit)
    request = BuildTasksRequest(
        records=records,
        source_edge_node=f'{definition.service_name}-trainer',
        target_services=[definition.service_name],
        deadline_ms=3000,
    )
    return build_tasks(request).generated_tasks


def last_value(task, field: str) -> float:
    return float(getattr(task.features, field)[-1])


def delta_value(task, field: str) -> float:
    values = [float(v) for v in getattr(task.features, field)]
    return values[-1] - values[0]


def weak_score(task, fields: list[str]) -> float:
    parts = []
    for field in fields:
        parts.append(abs(last_value(task, field)))
        parts.append(abs(delta_value(task, field)))
    return sum(parts) / max(len(parts), 1)


def threshold(scores: list[float], percentile: float) -> float:
    ordered = sorted(scores)
    index = max(int(percentile * len(ordered)) - 1, 0)
    return ordered[index]


def base_metadata(definition: ServiceDefinition, dataset_path: str | Path, training_samples: int) -> dict:
    return {
        'service_name': definition.service_name,
        'model_name': definition.model_name,
        'model_version': definition.model_version,
        'training_samples': training_samples,
        'dataset_path': str(dataset_path),
        'window_length': definition.window_length,
        'task_type': definition.task_type,
        'input_fields': definition.input_fields,
    }


def train_isolation_service(definition: ServiceDefinition, dataset_path: str | Path, limit: int | None = None) -> dict:
    tasks = build_training_tasks(definition, dataset_path, limit=limit)
    vectors = [make_feature_vector(task) for task in tasks]
    metadata = base_metadata(definition, dataset_path, len(vectors))
    model = IsolationForest(random_state=42, contamination=0.1)
    model.fit(vectors)
    scores = [-float(score) for score in model.score_samples(vectors)]
    metadata['threshold'] = threshold(scores, 0.9)
    save_model(definition.service_name, model, metadata)
    return metadata


def train_forecast_service(definition: ServiceDefinition, dataset_path: str | Path, limit: int | None = None) -> dict:
    tasks = build_training_tasks(definition, dataset_path, limit=limit)
    usable_tasks = tasks[:-1]
    future_tasks = tasks[1:]
    target_field = definition.target_field or definition.input_fields[0]
    features = [make_feature_vector(task) for task in usable_tasks]
    targets = [last_value(task, target_field) for task in future_tasks]
    usable = min(len(features), len(targets))
    features = features[:usable]
    targets = targets[:usable]
    metadata = base_metadata(definition, dataset_path, len(features))
    metadata['target_field'] = target_field
    model = LGBMRegressor(random_state=42, n_estimators=50, learning_rate=0.1, max_depth=4)
    model.fit(features, targets)
    save_model(definition.service_name, model, metadata)
    return metadata


def train_classifier_service(definition: ServiceDefinition, dataset_path: str | Path, limit: int | None = None) -> dict:
    tasks = build_training_tasks(definition, dataset_path, limit=limit)
    vectors = [make_feature_vector(task) for task in tasks]
    weak_fields = definition.weak_label_fields or definition.input_fields[:1]
    weak_scores = [weak_score(task, weak_fields) for task in tasks]
    positive_threshold = threshold(weak_scores, 0.8)
    labels = [1 if score >= positive_threshold else 0 for score in weak_scores]
    metadata = base_metadata(definition, dataset_path, len(vectors))
    metadata['threshold'] = 0.5
    metadata['weak_label_threshold'] = positive_threshold
    metadata['positive_ratio'] = sum(labels) / max(len(labels), 1)
    model = XGBClassifier(random_state=42)
    model.fit(vectors, labels)
    save_model(definition.service_name, model, metadata)
    return metadata

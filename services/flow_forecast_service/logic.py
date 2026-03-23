from __future__ import annotations

import csv
import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from statistics import mean, pstdev


@dataclass(frozen=True)
class ServiceDefinition:
    service_name: str
    task_type: str
    window_length: int
    input_fields: list[str]
    model_name: str
    model_version: str
    target_field: str | None = None


SERVICE_DEFINITION = ServiceDefinition(
    service_name='flow_forecast_service',
    task_type='forecast',
    window_length=24,
    input_fields=['flow_m3s', 'rain_intensity_mmph', 'temp_C'],
    model_name='FlowForecastRidge',
    model_version='v2',
    target_field='flow_m3s',
)

_REQUIRED_FIELDS = ['ts', 'slot', 'node_id', 'flow_m3s', 'rain_intensity_mmph', 'temp_C']


def _service_dir() -> Path:
    return Path(__file__).resolve().parent


def _default_artifact_dir() -> Path:
    return Path(os.environ.get('MODEL_DIR', _service_dir() / 'artifacts'))


def _artifact_dir(output_dir: str | Path | None = None) -> Path:
    return Path(output_dir) if output_dir is not None else _default_artifact_dir()


def _model_path(output_dir: str | Path | None = None) -> Path:
    return _artifact_dir(output_dir) / f'{SERVICE_DEFINITION.service_name}.joblib'


def _metadata_path(output_dir: str | Path | None = None) -> Path:
    return _artifact_dir(output_dir) / f'{SERVICE_DEFINITION.service_name}.metadata.json'


def _safe_div(numerator: float, denominator: float) -> float:
    if abs(denominator) < 1e-9:
        return 0.0
    return float(numerator / denominator)


def _std(values: list[float]) -> float:
    if len(values) <= 1:
        return 0.0
    return float(pstdev(values))


def _slope(values: list[float]) -> float:
    if len(values) <= 1:
        return 0.0
    return float((values[-1] - values[0]) / (len(values) - 1))


def _load_records(dataset_path: str | Path, limit: int | None = None) -> list[dict[str, str]]:
    dataset = Path(dataset_path)
    if not dataset.exists():
        raise FileNotFoundError(f'dataset not found: {dataset}')
    with dataset.open('r', encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        rows = []
        for index, row in enumerate(reader):
            normalized = {key.lstrip('\ufeff'): value for key, value in row.items()}
            rows.append(normalized)
            if limit is not None and index + 1 >= limit:
                break
    return rows


def _window_to_request(window: list[dict[str, str]], task_id: str) -> dict:
    features = {field: [row[field] for row in window] for field in _REQUIRED_FIELDS}
    return {
        'task_id': task_id,
        'service_name': SERVICE_DEFINITION.service_name,
        'source_edge_node': 'standalone-edge-node',
        'source_data_node': window[-1]['node_id'],
        'window_start': window[0]['ts'],
        'window_end': window[-1]['ts'],
        'deadline_ms': 3000,
        'features': features,
    }


def _build_requests(dataset_path: str | Path, limit: int | None = None) -> list[dict]:
    rows = _load_records(dataset_path, limit=limit)
    window_length = SERVICE_DEFINITION.window_length
    if len(rows) < window_length + 1:
        raise ValueError(f'not enough records for {SERVICE_DEFINITION.service_name}: need at least {window_length + 1}')
    requests = []
    for start in range(0, len(rows) - window_length + 1):
        window = rows[start:start + window_length]
        requests.append(_window_to_request(window, f'{SERVICE_DEFINITION.service_name}-{start + 1}'))
    return requests


def _feature_vector(request: dict) -> tuple[list[str], list[float]]:
    features = request['features']
    flow = [float(value) for value in features['flow_m3s']]
    rain = [float(value) for value in features['rain_intensity_mmph']]
    temp = [float(value) for value in features['temp_C']]
    last3_flow = flow[-3:]
    last3_rain = rain[-3:]
    names = [
        'bias',
        'flow_last', 'flow_lag_1', 'flow_lag_2', 'flow_mean', 'flow_std', 'flow_delta', 'flow_slope',
        'rain_last', 'rain_mean', 'rain_accum', 'rain_delta',
        'temp_last', 'temp_mean', 'temp_delta',
        'flow_rain_coupling', 'flow_temp_coupling',
    ]
    values = [
        1.0,
        float(flow[-1]),
        float(last3_flow[-2]) if len(last3_flow) >= 2 else float(flow[-1]),
        float(last3_flow[-3]) if len(last3_flow) >= 3 else float(flow[-1]),
        float(mean(flow)),
        _std(flow),
        float(flow[-1] - flow[0]),
        _slope(flow),
        float(rain[-1]),
        float(mean(rain)),
        float(sum(last3_rain)),
        float(rain[-1] - rain[0]),
        float(temp[-1]),
        float(mean(temp)),
        float(temp[-1] - temp[0]),
        _safe_div(flow[-1], rain[-1] + 1.0),
        _safe_div(flow[-1], temp[-1] + 1.0),
    ]
    return names, values


def _solve_linear_system(matrix: list[list[float]], targets: list[float]) -> list[float]:
    size = len(targets)
    augmented = [row[:] + [targets[index]] for index, row in enumerate(matrix)]
    for pivot in range(size):
        pivot_row = max(range(pivot, size), key=lambda row: abs(augmented[row][pivot]))
        augmented[pivot], augmented[pivot_row] = augmented[pivot_row], augmented[pivot]
        pivot_value = augmented[pivot][pivot]
        if abs(pivot_value) < 1e-12:
            continue
        augmented[pivot] = [value / pivot_value for value in augmented[pivot]]
        for row in range(size):
            if row == pivot:
                continue
            factor = augmented[row][pivot]
            augmented[row] = [
                current - factor * pivoted
                for current, pivoted in zip(augmented[row], augmented[pivot])
            ]
    return [row[-1] for row in augmented]


def _write_artifacts(model: dict, metadata: dict, output_dir: str | Path | None = None) -> None:
    target_dir = _artifact_dir(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    _model_path(target_dir).write_text(json.dumps(model, indent=2, ensure_ascii=False), encoding='utf-8')
    _metadata_path(target_dir).write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding='utf-8')


def _write_compatibility_copy(model: dict, metadata: dict, output_dir: str | Path | None) -> None:
    default_dir = _default_artifact_dir()
    if output_dir is None or Path(output_dir) == default_dir:
        return
    _write_artifacts(model, metadata, default_dir)


def train(dataset_path: str, limit: int | None = None, output_dir: str | Path | None = None) -> dict:
    requests = _build_requests(dataset_path, limit=limit)
    usable_requests = requests[:-1]
    future_requests = requests[1:]
    feature_names, _ = _feature_vector(usable_requests[0])
    rows = [_feature_vector(request)[1] for request in usable_requests]
    targets = [float(request['features']['flow_m3s'][-1]) for request in future_requests]
    usable = min(len(rows), len(targets))
    rows = rows[:usable]
    targets = targets[:usable]
    size = len(feature_names)
    ridge = 0.05
    xtx = [[0.0 for _ in range(size)] for _ in range(size)]
    xty = [0.0 for _ in range(size)]
    for row, target in zip(rows, targets):
        for i in range(size):
            xty[i] += row[i] * target
            for j in range(size):
                xtx[i][j] += row[i] * row[j]
    for index in range(1, size):
        xtx[index][index] += ridge
    weights = _solve_linear_system(xtx, xty)
    predictions = [sum(weight * value for weight, value in zip(weights, row)) for row in rows]
    errors = [target - prediction for target, prediction in zip(targets, predictions)]
    mae = float(mean(abs(error) for error in errors)) if errors else 0.0
    model = {
        'type': 'flow_forecast_ridge',
        'feature_names': feature_names,
        'weights': weights,
    }
    metadata = {
        'service_name': SERVICE_DEFINITION.service_name,
        'model_name': SERVICE_DEFINITION.model_name,
        'model_version': SERVICE_DEFINITION.model_version,
        'task_type': SERVICE_DEFINITION.task_type,
        'window_length': SERVICE_DEFINITION.window_length,
        'input_fields': SERVICE_DEFINITION.input_fields,
        'target_field': SERVICE_DEFINITION.target_field,
        'dataset_path': str(dataset_path),
        'training_samples': len(rows),
        'train_mae': mae,
        'artifact_dir': str(_artifact_dir(output_dir)),
    }
    _write_artifacts(model, metadata, output_dir)
    _write_compatibility_copy(model, metadata, output_dir)
    return metadata


def _load_artifacts(output_dir: str | Path | None = None) -> tuple[dict, dict]:
    model_path = _model_path(output_dir)
    metadata_path = _metadata_path(output_dir)
    if not model_path.exists():
        raise FileNotFoundError(f'model not found: {model_path}. train the service first via CLI or POST /train')
    if not metadata_path.exists():
        raise FileNotFoundError(f'metadata not found: {metadata_path}. train the service first via CLI or POST /train')
    model = json.loads(model_path.read_text(encoding='utf-8'))
    metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
    return model, metadata


def meta() -> dict:
    payload = asdict(SERVICE_DEFINITION)
    metadata_path = _metadata_path()
    payload['artifact_dir'] = str(_artifact_dir())
    payload['model_ready'] = metadata_path.exists()
    if metadata_path.exists():
        stored = json.loads(metadata_path.read_text(encoding='utf-8'))
        payload['trained_dataset_path'] = stored.get('dataset_path')
        payload['training_samples'] = stored.get('training_samples')
        payload['train_mae'] = stored.get('train_mae')
    return payload


def predict(request: dict, output_dir: str | Path | None = None) -> dict:
    model, metadata = _load_artifacts(output_dir)
    _, vector = _feature_vector(request)
    prediction = sum(weight * value for weight, value in zip(model['weights'], vector))
    return {
        'task_id': request['task_id'],
        'service_name': SERVICE_DEFINITION.service_name,
        'result_type': 'forecast',
        'prediction': max(float(prediction), 0.0),
        'model_name': metadata['model_name'],
        'model_version': metadata['model_version'],
        'inference_ms': 0,
    }

from __future__ import annotations

import csv
import json
import os
from dataclasses import asdict, dataclass
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


SERVICE_DEFINITION = ServiceDefinition(
    service_name='flow_anomaly_service',
    task_type='anomaly',
    window_length=12,
    input_fields=['flow_m3s', 'rain_intensity_mmph', 'temp_C'],
    model_name='FlowAnomalyBaseline',
    model_version='v2',
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
            rows.append({key.lstrip('\ufeff'): value for key, value in row.items()})
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
    if len(rows) < window_length:
        raise ValueError(f'not enough records for {SERVICE_DEFINITION.service_name}: need at least {window_length}')
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

    flow_mean = float(mean(flow))
    rain_mean = float(mean(rain))
    temp_mean = float(mean(temp))

    names = [
        'flow_mean', 'flow_std', 'flow_last', 'flow_delta', 'flow_min', 'flow_max', 'flow_slope',
        'rain_mean', 'rain_last', 'rain_accum', 'rain_delta',
        'temp_mean', 'temp_last', 'temp_delta',
        'flow_rain_ratio', 'flow_temp_ratio', 'peak_to_average',
    ]
    values = [
        flow_mean,
        _std(flow),
        float(flow[-1]),
        float(flow[-1] - flow[0]),
        float(min(flow)),
        float(max(flow)),
        _slope(flow),
        rain_mean,
        float(rain[-1]),
        float(sum(rain)),
        float(rain[-1] - rain[0]),
        temp_mean,
        float(temp[-1]),
        float(temp[-1] - temp[0]),
        _safe_div(flow_mean, rain_mean + 1.0),
        _safe_div(flow_mean, temp_mean + 1.0),
        _safe_div(max(flow), flow_mean + 1e-6),
    ]
    return names, values


def _anomaly_score(vector: list[float], means: list[float], scales: list[float]) -> float:
    return float(mean(abs(value - center) / scale for value, center, scale in zip(vector, means, scales)))


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    index = max(int(percentile * len(ordered)) - 1, 0)
    return float(ordered[index])


def _write_artifacts(model: dict, metadata: dict, output_dir: str | Path | None = None) -> None:
    target_dir = _artifact_dir(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    _model_path(target_dir).write_text(json.dumps(model, indent=2, ensure_ascii=False), encoding='utf-8')
    _metadata_path(target_dir).write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding='utf-8')


def train(dataset_path: str, limit: int | None = None, output_dir: str | Path | None = None) -> dict:
    requests = _build_requests(dataset_path, limit=limit)
    feature_names, _ = _feature_vector(requests[0])
    vectors = [_feature_vector(request)[1] for request in requests]

    means = [float(mean(row[index] for row in vectors)) for index in range(len(feature_names))]
    scales = []
    for index in range(len(feature_names)):
        spread = _std([row[index] for row in vectors])
        scales.append(spread if spread > 1e-6 else 1.0)

    training_scores = [_anomaly_score(row, means, scales) for row in vectors]
    threshold = _percentile(training_scores, 0.92)

    model = {
        'type': 'flow_anomaly_baseline',
        'feature_names': feature_names,
        'feature_means': means,
        'feature_scales': scales,
        'threshold': threshold,
        'training_score_mean': float(mean(training_scores)),
        'training_score_std': _std(training_scores) or 1.0,
    }
    metadata = {
        'service_name': SERVICE_DEFINITION.service_name,
        'model_name': SERVICE_DEFINITION.model_name,
        'model_version': SERVICE_DEFINITION.model_version,
        'task_type': SERVICE_DEFINITION.task_type,
        'window_length': SERVICE_DEFINITION.window_length,
        'input_fields': SERVICE_DEFINITION.input_fields,
        'dataset_path': str(dataset_path),
        'training_samples': len(vectors),
        'threshold': threshold,
        'artifact_dir': str(_artifact_dir(output_dir)),
    }

    _write_artifacts(model, metadata, output_dir)
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
    return payload


def _validate_request(request: dict) -> None:
    if request.get('service_name') != SERVICE_DEFINITION.service_name:
        raise ValueError(f"service_name must be '{SERVICE_DEFINITION.service_name}'")
    features = request.get('features')
    if not isinstance(features, dict):
        raise ValueError('features must be an object')
    for field in _REQUIRED_FIELDS:
        if field not in features:
            raise ValueError(f'missing features.{field}')
    lengths = [len(features[field]) for field in _REQUIRED_FIELDS]
    if len(set(lengths)) != 1:
        raise ValueError(f'feature lengths must match, got {lengths}')
    if lengths[0] != SERVICE_DEFINITION.window_length:
        raise ValueError(f'window length must be {SERVICE_DEFINITION.window_length}, got {lengths[0]}')


def predict(request: dict, output_dir: str | Path | None = None) -> dict:
    _validate_request(request)
    model, metadata = _load_artifacts(output_dir)
    _, vector = _feature_vector(request)
    score = _anomaly_score(vector, model['feature_means'], model['feature_scales'])
    return {
        'task_id': request['task_id'],
        'service_name': SERVICE_DEFINITION.service_name,
        'result_type': 'anomaly',
        'score': score,
        'label': 'abnormal' if score >= float(model['threshold']) else 'normal',
        'model_name': metadata['model_name'],
        'model_version': metadata['model_version'],
        'inference_ms': 0,
    }

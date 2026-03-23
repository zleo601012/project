from __future__ import annotations

from pathlib import Path
from statistics import mean, pstdev

from shared.ml.model_io import save_model
from shared.schemas.common import AnomalyResponse, BuildTasksRequest, ForecastResponse, InferRequest
from shared.utils.dataset import load_records
from shared.utils.windowing import build_tasks


def _build_tasks(service_name: str, dataset_path: str | Path, window_length: int, limit: int | None = None):
    records = load_records(dataset_path, limit=limit)
    request = BuildTasksRequest(
        records=records,
        source_edge_node=f'{service_name}-trainer',
        target_services=[service_name],
        deadline_ms=3000,
    )
    return build_tasks(request).generated_tasks


def _std(values: list[float]) -> float:
    if len(values) <= 1:
        return 0.0
    return float(pstdev(values))


def _slope(values: list[float]) -> float:
    if len(values) <= 1:
        return 0.0
    return float((values[-1] - values[0]) / (len(values) - 1))


def _safe_div(numerator: float, denominator: float) -> float:
    if abs(denominator) < 1e-9:
        return 0.0
    return float(numerator / denominator)


def flow_anomaly_feature_vector(request: InferRequest) -> tuple[list[str], list[float]]:
    flow = [float(v) for v in request.features.flow_m3s]
    rain = [float(v) for v in request.features.rain_intensity_mmph]
    temp = [float(v) for v in request.features.temp_C]
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
    z_scores = [abs(value - center) / scale for value, center, scale in zip(vector, means, scales)]
    return float(mean(z_scores))


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    index = max(int(percentile * len(ordered)) - 1, 0)
    return float(ordered[index])


def train_flow_anomaly_service(service_name: str, dataset_path: str | Path, window_length: int, limit: int | None = None) -> dict:
    tasks = _build_tasks(service_name, dataset_path, window_length, limit=limit)
    feature_names, _ = flow_anomaly_feature_vector(tasks[0])
    vectors = [flow_anomaly_feature_vector(task)[1] for task in tasks]
    means = [float(mean(row[idx] for row in vectors)) for idx in range(len(feature_names))]
    scales = []
    for idx in range(len(feature_names)):
        spread = _std([row[idx] for row in vectors])
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
        'service_name': service_name,
        'model_name': 'FlowAnomalyBaseline',
        'model_version': 'v2',
        'training_samples': len(vectors),
        'dataset_path': str(dataset_path),
        'window_length': window_length,
        'task_type': 'anomaly',
        'input_fields': ['flow_m3s', 'rain_intensity_mmph', 'temp_C'],
        'feature_names': feature_names,
        'threshold': threshold,
    }
    save_model(service_name, model, metadata)
    return metadata


def predict_flow_anomaly(model: dict, metadata: dict, request: InferRequest) -> AnomalyResponse:
    _, vector = flow_anomaly_feature_vector(request)
    score = _anomaly_score(vector, model['feature_means'], model['feature_scales'])
    label = 'abnormal' if score >= float(model['threshold']) else 'normal'
    return AnomalyResponse(
        task_id=request.task_id,
        service_name=request.service_name,
        score=score,
        label=label,
        model_name=metadata['model_name'],
        model_version=metadata['model_version'],
        inference_ms=0,
    )


def flow_forecast_feature_vector(request: InferRequest) -> tuple[list[str], list[float]]:
    flow = [float(v) for v in request.features.flow_m3s]
    rain = [float(v) for v in request.features.rain_intensity_mmph]
    temp = [float(v) for v in request.features.temp_C]
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
    augmented = [row[:] + [targets[idx]] for idx, row in enumerate(matrix)]
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


def train_flow_forecast_service(service_name: str, dataset_path: str | Path, window_length: int, limit: int | None = None) -> dict:
    tasks = _build_tasks(service_name, dataset_path, window_length, limit=limit)
    usable_tasks = tasks[:-1]
    future_tasks = tasks[1:]
    feature_names, _ = flow_forecast_feature_vector(usable_tasks[0])
    rows = [flow_forecast_feature_vector(task)[1] for task in usable_tasks]
    targets = [float(task.features.flow_m3s[-1]) for task in future_tasks]
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
    for idx in range(1, size):
        xtx[idx][idx] += ridge
    weights = _solve_linear_system(xtx, xty)
    predictions = [sum(weight * value for weight, value in zip(weights, row)) for row in rows]
    errors = [target - prediction for target, prediction in zip(targets, predictions)]
    mae = float(mean(abs(err) for err in errors)) if errors else 0.0
    model = {
        'type': 'flow_forecast_ridge',
        'feature_names': feature_names,
        'weights': weights,
    }
    metadata = {
        'service_name': service_name,
        'model_name': 'FlowForecastRidge',
        'model_version': 'v2',
        'training_samples': len(rows),
        'dataset_path': str(dataset_path),
        'window_length': window_length,
        'task_type': 'forecast',
        'input_fields': ['flow_m3s', 'rain_intensity_mmph', 'temp_C'],
        'target_field': 'flow_m3s',
        'feature_names': feature_names,
        'train_mae': mae,
    }
    save_model(service_name, model, metadata)
    return metadata


def predict_flow_forecast(model: dict, metadata: dict, request: InferRequest) -> ForecastResponse:
    _, vector = flow_forecast_feature_vector(request)
    prediction = sum(weight * value for weight, value in zip(model['weights'], vector))
    prediction = max(float(prediction), 0.0)
    return ForecastResponse(
        task_id=request.task_id,
        service_name=request.service_name,
        prediction=prediction,
        model_name=metadata['model_name'],
        model_version=metadata['model_version'],
        inference_ms=0,
    )

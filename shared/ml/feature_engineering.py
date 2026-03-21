from __future__ import annotations

from statistics import mean, pstdev
from shared.config.service_catalog import SERVICE_CATALOG
from shared.schemas.common import InferRequest


def _summary(values: list[float]) -> dict[str, float]:
    if len(values) == 1:
        deviation = 0.0
    else:
        deviation = pstdev(values)
    return {
        'mean': float(mean(values)),
        'std': float(deviation),
        'min': float(min(values)),
        'max': float(max(values)),
        'last': float(values[-1]),
        'delta': float(values[-1] - values[0]),
    }


def make_feature_vector(request: InferRequest) -> list[float]:
    definition = SERVICE_CATALOG[request.service_name]
    vector: list[float] = []
    for field in definition.input_fields:
        stats = _summary([float(v) for v in getattr(request.features, field)])
        vector.extend(stats.values())
    return vector


def make_forecast_target(window_flow: list[float]) -> float:
    return float(window_flow[-1])

from __future__ import annotations

from shared.ml.feature_engineering import make_feature_vector
from shared.schemas.common import AnomalyResponse, InferRequest


def predict(model, metadata: dict, request: InferRequest) -> AnomalyResponse:
    vector = make_feature_vector(request)
    raw_score = float(-model.score_samples([vector])[0])
    threshold = float(metadata.get('threshold', 0.5))
    label = 'abnormal' if raw_score >= threshold else 'normal'
    return AnomalyResponse(
        task_id=request.task_id,
        service_name=request.service_name,
        score=raw_score,
        label=label,
        model_name=metadata['model_name'],
        model_version=metadata['model_version'],
        inference_ms=0,
    )

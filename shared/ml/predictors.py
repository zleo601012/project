from __future__ import annotations

from shared.ml.feature_engineering import make_feature_vector
from shared.schemas.common import AnomalyResponse, ForecastResponse, InferRequest, RiskScoreResponse


def _probability_from_classifier(model, vector: list[float]) -> float:
    probabilities = model.predict_proba([vector])[0]
    return float(probabilities[-1])


def predict_anomaly(model, metadata: dict, request: InferRequest) -> AnomalyResponse:
    vector = make_feature_vector(request)
    if metadata['model_name'] == 'IsolationForest':
        raw_score = float(-model.score_samples([vector])[0])
        threshold = float(metadata.get('threshold', 0.5))
        label = 'abnormal' if raw_score >= threshold else 'normal'
        score = raw_score
    else:
        score = _probability_from_classifier(model, vector)
        label = 'abnormal' if score >= float(metadata.get('threshold', 0.5)) else 'normal'
    return AnomalyResponse(
        task_id=request.task_id,
        service_name=request.service_name,
        score=score,
        label=label,
        model_name=metadata['model_name'],
        model_version=metadata['model_version'],
        inference_ms=0,
    )


def predict_forecast(model, metadata: dict, request: InferRequest) -> ForecastResponse:
    vector = make_feature_vector(request)
    prediction = float(model.predict([vector])[0])
    return ForecastResponse(
        task_id=request.task_id,
        service_name=request.service_name,
        prediction=prediction,
        model_name=metadata['model_name'],
        model_version=metadata['model_version'],
        inference_ms=0,
    )


def predict_risk_score(model, metadata: dict, request: InferRequest) -> RiskScoreResponse:
    vector = make_feature_vector(request)
    score = _probability_from_classifier(model, vector)
    if score >= 0.66:
        label = 'high'
    elif score >= 0.33:
        label = 'medium'
    else:
        label = 'low'
    return RiskScoreResponse(
        task_id=request.task_id,
        service_name=request.service_name,
        risk_score=score,
        label=label,
        model_name=metadata['model_name'],
        model_version=metadata['model_version'],
        inference_ms=0,
    )

from __future__ import annotations

from shared.ml.feature_engineering import make_feature_vector
from shared.schemas.common import ForecastResponse, InferRequest


def predict(model, metadata: dict, request: InferRequest) -> ForecastResponse:
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

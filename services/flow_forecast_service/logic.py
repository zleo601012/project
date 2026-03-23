from __future__ import annotations

from shared.config.service_definition import ServiceDefinition
from shared.ml.predictors import predict_forecast
from shared.ml.service_logic import train_forecast_service

SERVICE_DEFINITION = ServiceDefinition(
    service_name='flow_forecast_service',
    task_type='forecast',
    window_length=24,
    input_fields=['flow_m3s', 'rain_intensity_mmph', 'temp_C'],
    model_name='LightGBMRegressor',
    target_field='flow_m3s',
)

predict = predict_forecast


def train(dataset_path: str, limit: int | None = None):
    return train_forecast_service(SERVICE_DEFINITION, dataset_path, limit=limit)

from __future__ import annotations

from shared.config.service_definition import ServiceDefinition
from shared.ml.phase1_models import predict_flow_forecast, train_flow_forecast_service

SERVICE_DEFINITION = ServiceDefinition(
    service_name='flow_forecast_service',
    task_type='forecast',
    window_length=24,
    input_fields=['flow_m3s', 'rain_intensity_mmph', 'temp_C'],
    model_name='FlowForecastRidge',
    target_field='flow_m3s',
    model_version='v2',
)

predict = predict_flow_forecast


def train(dataset_path: str, limit: int | None = None):
    return train_flow_forecast_service(
        SERVICE_DEFINITION.service_name,
        dataset_path,
        SERVICE_DEFINITION.window_length,
        limit=limit,
    )

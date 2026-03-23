from __future__ import annotations

from shared.config.service_definition import ServiceDefinition
from shared.ml.phase1_models import predict_flow_anomaly, train_flow_anomaly_service
from shared.ml.predictors import predict_anomaly
from shared.ml.service_logic import train_isolation_service

SERVICE_DEFINITION = ServiceDefinition(
    service_name='flow_anomaly_service',
    task_type='anomaly',
    window_length=12,
    input_fields=['flow_m3s', 'rain_intensity_mmph', 'temp_C'],
    model_name='FlowAnomalyBaseline',
    weak_label_fields=['flow_m3s'],
    model_version='v2',
)

predict = predict_flow_anomaly


def train(dataset_path: str, limit: int | None = None):
    return train_flow_anomaly_service(
        SERVICE_DEFINITION.service_name,
        dataset_path,
        SERVICE_DEFINITION.window_length,
        limit=limit,
    )
    model_name='IsolationForest',
    weak_label_fields=['flow_m3s'],
)

predict = predict_anomaly


def train(dataset_path: str, limit: int | None = None):
    return train_isolation_service(SERVICE_DEFINITION, dataset_path, limit=limit)

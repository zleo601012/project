from __future__ import annotations

from shared.config.service_definition import ServiceDefinition
from shared.ml.predictors import predict_anomaly
from shared.ml.service_logic import train_classifier_service

SERVICE_DEFINITION = ServiceDefinition(
    service_name='cod_anomaly_service',
    task_type='anomaly',
    window_length=12,
    input_fields=['COD_mgL', 'flow_m3s', 'rain_intensity_mmph', 'temp_C'],
    model_name='XGBoostClassifier',
    weak_label_fields=['COD_mgL'],
)

predict = predict_anomaly


def train(dataset_path: str, limit: int | None = None):
    return train_classifier_service(SERVICE_DEFINITION, dataset_path, limit=limit)

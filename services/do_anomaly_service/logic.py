from __future__ import annotations

from shared.config.service_definition import ServiceDefinition
from shared.ml.predictors import predict_anomaly
from shared.ml.service_logic import train_classifier_service

SERVICE_DEFINITION = ServiceDefinition(
    service_name='do_anomaly_service',
    task_type='anomaly',
    window_length=12,
    input_fields=['DO_mgL', 'flow_m3s', 'temp_C', 'rain_intensity_mmph'],
    model_name='XGBoostClassifier',
    weak_label_fields=['DO_mgL'],
)

predict = predict_anomaly


def train(dataset_path: str, limit: int | None = None):
    return train_classifier_service(SERVICE_DEFINITION, dataset_path, limit=limit)

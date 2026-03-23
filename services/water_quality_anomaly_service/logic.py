from __future__ import annotations

from shared.config.service_definition import ServiceDefinition
from shared.ml.predictors import predict_anomaly
from shared.ml.service_logic import train_isolation_service

SERVICE_DEFINITION = ServiceDefinition(
    service_name='water_quality_anomaly_service',
    task_type='anomaly',
    window_length=12,
    input_fields=['pH', 'DO_mgL', 'EC_uScm', 'COD_mgL', 'NH3N_mgL', 'TN_mgL', 'TP_mgL', 'TSS_mgL', 'turbidity_NTU'],
    model_name='IsolationForest',
    weak_label_fields=['COD_mgL', 'NH3N_mgL', 'TP_mgL', 'TSS_mgL', 'turbidity_NTU'],
)

predict = predict_anomaly


def train(dataset_path: str, limit: int | None = None):
    return train_isolation_service(SERVICE_DEFINITION, dataset_path, limit=limit)

from __future__ import annotations

from shared.config.service_definition import ServiceDefinition
from shared.ml.predictors import predict_risk_score
from shared.ml.service_logic import train_classifier_service

SERVICE_DEFINITION = ServiceDefinition(
    service_name='mixed_sewage_rain_score_service',
    task_type='risk_score',
    window_length=12,
    input_fields=['rain_intensity_mmph', 'flow_m3s', 'COD_mgL', 'NH3N_mgL', 'TSS_mgL', 'turbidity_NTU'],
    model_name='XGBoostClassifier',
    weak_label_fields=['rain_intensity_mmph', 'flow_m3s', 'COD_mgL', 'NH3N_mgL', 'TSS_mgL', 'turbidity_NTU'],
)

predict = predict_risk_score


def train(dataset_path: str, limit: int | None = None):
    return train_classifier_service(SERVICE_DEFINITION, dataset_path, limit=limit)

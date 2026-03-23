from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

TaskType = Literal["anomaly", "forecast", "risk_score"]

ALL_DATA_FIELDS = [
    "ts", "slot", "node_id", "rain_intensity_mmph", "flow_m3s", "temp_C", "pH", "DO_mgL",
    "EC_uScm", "COD_mgL", "NH3N_mgL", "TN_mgL", "TP_mgL", "TSS_mgL", "turbidity_NTU",
]

@dataclass(frozen=True)
class ServiceDefinition:
    service_name: str
    task_type: TaskType
    window_length: int
    input_fields: list[str]
    model_name: str
    model_version: str = "v1"
    target_field: str | None = None
    weak_label_fields: list[str] | None = None

SERVICE_CATALOG: dict[str, ServiceDefinition] = {
    "flow_anomaly_service": ServiceDefinition(
        service_name="flow_anomaly_service",
        task_type="anomaly",
        window_length=12,
        input_fields=["flow_m3s", "rain_intensity_mmph", "temp_C"],
        model_name="IsolationForest",
        weak_label_fields=["flow_m3s"],
    ),
    "water_quality_anomaly_service": ServiceDefinition(
        service_name="water_quality_anomaly_service",
        task_type="anomaly",
        window_length=12,
        input_fields=["pH", "DO_mgL", "EC_uScm", "COD_mgL", "NH3N_mgL", "TN_mgL", "TP_mgL", "TSS_mgL", "turbidity_NTU"],
        model_name="IsolationForest",
        weak_label_fields=["COD_mgL", "NH3N_mgL", "TP_mgL", "TSS_mgL", "turbidity_NTU"],
    ),
    "cod_anomaly_service": ServiceDefinition(
        service_name="cod_anomaly_service",
        task_type="anomaly",
        window_length=12,
        input_fields=["COD_mgL", "flow_m3s", "rain_intensity_mmph", "temp_C"],
        model_name="XGBoostClassifier",
        weak_label_fields=["COD_mgL"],
    ),
    "nh3n_anomaly_service": ServiceDefinition(
        service_name="nh3n_anomaly_service",
        task_type="anomaly",
        window_length=12,
        input_fields=["NH3N_mgL", "flow_m3s", "rain_intensity_mmph", "temp_C"],
        model_name="XGBoostClassifier",
        weak_label_fields=["NH3N_mgL"],
    ),
    "tss_turbidity_anomaly_service": ServiceDefinition(
        service_name="tss_turbidity_anomaly_service",
        task_type="anomaly",
        window_length=12,
        input_fields=["TSS_mgL", "turbidity_NTU", "flow_m3s", "rain_intensity_mmph"],
        model_name="XGBoostClassifier",
        weak_label_fields=["TSS_mgL", "turbidity_NTU"],
    ),
    "do_anomaly_service": ServiceDefinition(
        service_name="do_anomaly_service",
        task_type="anomaly",
        window_length=12,
        input_fields=["DO_mgL", "flow_m3s", "temp_C", "rain_intensity_mmph"],
        model_name="XGBoostClassifier",
        weak_label_fields=["DO_mgL"],
    ),
    "flow_forecast_service": ServiceDefinition(
        service_name="flow_forecast_service",
        task_type="forecast",
        window_length=24,
        input_fields=["flow_m3s", "rain_intensity_mmph", "temp_C"],
        model_name="LightGBMRegressor",
        target_field="flow_m3s",
    ),
    "cod_forecast_service": ServiceDefinition(
        service_name="cod_forecast_service",
        task_type="forecast",
        window_length=24,
        input_fields=["COD_mgL", "flow_m3s", "rain_intensity_mmph", "temp_C"],
        model_name="LightGBMRegressor",
        target_field="COD_mgL",
    ),
    "nh3n_forecast_service": ServiceDefinition(
        service_name="nh3n_forecast_service",
        task_type="forecast",
        window_length=24,
        input_fields=["NH3N_mgL", "flow_m3s", "rain_intensity_mmph", "temp_C"],
        model_name="LightGBMRegressor",
        target_field="NH3N_mgL",
    ),
    "tss_turbidity_forecast_service": ServiceDefinition(
        service_name="tss_turbidity_forecast_service",
        task_type="forecast",
        window_length=24,
        input_fields=["TSS_mgL", "turbidity_NTU", "flow_m3s", "rain_intensity_mmph"],
        model_name="LightGBMRegressor",
        target_field="TSS_mgL",
    ),
    "mixed_sewage_rain_score_service": ServiceDefinition(
        service_name="mixed_sewage_rain_score_service",
        task_type="risk_score",
        window_length=12,
        input_fields=["rain_intensity_mmph", "flow_m3s", "COD_mgL", "NH3N_mgL", "TSS_mgL", "turbidity_NTU"],
        model_name="XGBoostClassifier",
        weak_label_fields=["rain_intensity_mmph", "flow_m3s", "COD_mgL", "NH3N_mgL", "TSS_mgL", "turbidity_NTU"],
    ),
    "illegal_discharge_score_service": ServiceDefinition(
        service_name="illegal_discharge_score_service",
        task_type="risk_score",
        window_length=12,
        input_fields=["flow_m3s", "pH", "DO_mgL", "EC_uScm", "COD_mgL", "NH3N_mgL", "TN_mgL", "TP_mgL", "TSS_mgL", "turbidity_NTU"],
        model_name="XGBoostClassifier",
        weak_label_fields=["COD_mgL", "NH3N_mgL", "TN_mgL", "TP_mgL", "TSS_mgL", "turbidity_NTU"],
    ),
}

ANOMALY_SERVICES = [name for name, item in SERVICE_CATALOG.items() if item.task_type == 'anomaly']
FORECAST_SERVICES = [name for name, item in SERVICE_CATALOG.items() if item.task_type == 'forecast']
RISK_SCORE_SERVICES = [name for name, item in SERVICE_CATALOG.items() if item.task_type == 'risk_score']

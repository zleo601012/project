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

SERVICE_CATALOG: dict[str, ServiceDefinition] = {
    "flow_anomaly_service": ServiceDefinition(
        service_name="flow_anomaly_service",
        task_type="anomaly",
        window_length=12,
        input_fields=["flow_m3s", "rain_intensity_mmph", "temp_C"],
        model_name="IsolationForest",
    ),
    "flow_forecast_service": ServiceDefinition(
        service_name="flow_forecast_service",
        task_type="forecast",
        window_length=24,
        input_fields=["flow_m3s", "rain_intensity_mmph", "temp_C"],
        model_name="LightGBMRegressor",
    ),
}

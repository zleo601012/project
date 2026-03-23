from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator
from shared.config.data_fields import ALL_DATA_FIELDS

class FeatureWindow(BaseModel):
    ts: list[str]
    slot: list[int]
    node_id: list[str | int]
    rain_intensity_mmph: list[float]
    flow_m3s: list[float]
    temp_C: list[float]
    pH: list[float]
    DO_mgL: list[float]
    EC_uScm: list[float]
    COD_mgL: list[float]
    NH3N_mgL: list[float]
    TN_mgL: list[float]
    TP_mgL: list[float]
    TSS_mgL: list[float]
    turbidity_NTU: list[float]

    @model_validator(mode='after')
    def validate_lengths(self) -> 'FeatureWindow':
        lengths = {field: len(getattr(self, field)) for field in ALL_DATA_FIELDS}
        uniq = set(lengths.values())
        if len(uniq) != 1:
            raise ValueError(f'Feature lengths must match, got {lengths}')
        return self

    def length(self) -> int:
        return len(self.ts)

class InferRequest(BaseModel):
    task_id: str
    service_name: str
    source_edge_node: str
    source_data_node: str
    window_start: str
    window_end: str
    deadline_ms: int = Field(gt=0)
    features: FeatureWindow

    @model_validator(mode='after')
    def validate_service_window(self) -> 'InferRequest':
        from shared.config.service_catalog import SERVICE_CATALOG

        service = SERVICE_CATALOG.get(self.service_name)
        if service and self.features.length() != service.window_length:
            raise ValueError(
                f'{self.service_name} requires window length {service.window_length}, got {self.features.length()}'
            )
        return self

class BaseInferResponse(BaseModel):
    task_id: str
    service_name: str
    model_name: str
    model_version: str
    inference_ms: int

class AnomalyResponse(BaseInferResponse):
    result_type: Literal['anomaly'] = 'anomaly'
    score: float
    label: str

class ForecastResponse(BaseInferResponse):
    result_type: Literal['forecast'] = 'forecast'
    prediction: float

class RiskScoreResponse(BaseInferResponse):
    result_type: Literal['risk_score'] = 'risk_score'
    risk_score: float
    label: str

class ServiceMeta(BaseModel):
    service_name: str
    model_name: str
    model_version: str
    task_type: str
    window_length: int
    input_fields: list[str]

class ReplayRequest(BaseModel):
    dataset_path: str
    limit: int | None = Field(default=None, ge=1)
    speedup: float = Field(default=1.0, gt=0)
    emit_sleep: bool = False

class ReplayRecord(BaseModel):
    ts: str
    slot: int
    node_id: str
    rain_intensity_mmph: float
    flow_m3s: float
    temp_C: float
    pH: float
    DO_mgL: float
    EC_uScm: float
    COD_mgL: float
    NH3N_mgL: float
    TN_mgL: float
    TP_mgL: float
    TSS_mgL: float
    turbidity_NTU: float

class ReplayResponse(BaseModel):
    dataset_path: str
    emitted: int
    records: list[ReplayRecord]

class BuildTasksRequest(BaseModel):
    records: list[ReplayRecord]
    source_edge_node: str
    target_services: list[str]
    deadline_ms: int = Field(default=3000, gt=0)

class BuildTasksResponse(BaseModel):
    generated_tasks: list[InferRequest]

class TaskLogEntry(BaseModel):
    task_id: str
    service_name: str
    source_edge_node: str
    target_edge_node: str
    source_data_node: str
    window_start: str
    window_end: str
    submit_ts: datetime
    start_ts: datetime
    end_ts: datetime
    latency_ms: int
    queue_ms: int
    inference_ms: int
    status: str
    decision_type: str
    image_ready: bool
    image_pull_used: bool
    container_cold_start_used: bool
    extra: dict[str, Any] = Field(default_factory=dict)

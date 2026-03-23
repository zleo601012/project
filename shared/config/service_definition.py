from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

TaskType = Literal['anomaly', 'forecast', 'risk_score']


@dataclass(frozen=True)
class ServiceDefinition:
    service_name: str
    task_type: TaskType
    window_length: int
    input_fields: list[str]
    model_name: str
    model_version: str = 'v1'
    target_field: str | None = None
    weak_label_fields: list[str] | None = None

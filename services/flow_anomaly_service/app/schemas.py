from __future__ import annotations

from typing import List

from pydantic import BaseModel, validator

from .config import settings


class WindowPoint(BaseModel):
    flow_m3s: float
    rain_intensity_mmph: float
    temp_C: float


class DetectRequest(BaseModel):
    window: List[WindowPoint]

    @validator("window")
    def validate_window_length(cls, value: List[WindowPoint]) -> List[WindowPoint]:
        if len(value) != settings.window_length:
            raise ValueError(f"window length must be exactly {settings.window_length}")
        return value


class DetectResponse(BaseModel):
    is_anomaly: bool
    anomaly_score: float
    threshold: float
    reconstruction_error: float
    model_name: str
    window_length: int

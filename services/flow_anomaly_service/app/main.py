from __future__ import annotations

from fastapi import FastAPI

from .schemas import DetectRequest, DetectResponse
from .service import FlowAnomalyDetector

app = FastAPI(title="flow_anomaly_service", version="0.1.0")

detector = FlowAnomalyDetector()


@app.on_event("startup")
def startup_event() -> None:
    detector.load()


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.post("/detect", response_model=DetectResponse)
def detect(payload: DetectRequest) -> DetectResponse:
    result = detector.detect([point.dict() for point in payload.window])
    return DetectResponse(**result)

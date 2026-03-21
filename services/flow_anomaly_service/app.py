from __future__ import annotations

from services.flow_anomaly_service.inference import predict
from shared.service_base import create_inference_app

app = create_inference_app('flow_anomaly_service', predict)

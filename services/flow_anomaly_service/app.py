from __future__ import annotations

from shared.ml.predictors import predict_anomaly
from shared.service_base import create_inference_app

app = create_inference_app('flow_anomaly_service', predict_anomaly)

from __future__ import annotations

from shared.ml.predictors import predict_risk_score
from shared.service_base import create_inference_app

app = create_inference_app('illegal_discharge_score_service', predict_risk_score)

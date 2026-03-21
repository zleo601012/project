from __future__ import annotations

from shared.ml.predictors import predict_risk_score
from shared.service_base import create_inference_app

app = create_inference_app('mixed_sewage_rain_score_service', predict_risk_score)

from __future__ import annotations

from shared.ml.predictors import predict_forecast
from shared.service_base import create_inference_app

app = create_inference_app('cod_forecast_service', predict_forecast)

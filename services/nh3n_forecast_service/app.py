from __future__ import annotations

from services.nh3n_forecast_service.logic import SERVICE_DEFINITION, predict
from shared.service_base import create_inference_app

app = create_inference_app(SERVICE_DEFINITION.service_name, predict)

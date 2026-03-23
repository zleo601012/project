from __future__ import annotations

from services.mixed_sewage_rain_score_service.logic import SERVICE_DEFINITION, predict
from shared.service_base import create_inference_app

app = create_inference_app(SERVICE_DEFINITION.service_name, predict)

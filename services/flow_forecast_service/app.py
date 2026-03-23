from __future__ import annotations

from services.flow_forecast_service.logic import SERVICE_DEFINITION, meta, predict, train
from services.flow_forecast_service.runtime import App

app = App(title=SERVICE_DEFINITION.service_name)


@app.get('/health')
def health() -> dict:
    return {'status': 'ok', 'service_name': SERVICE_DEFINITION.service_name}


@app.get('/meta')
def service_meta() -> dict:
    return meta()


@app.post('/train')
def train_model(payload: dict) -> dict:
    dataset_path = payload.get('dataset_path')
    if not dataset_path:
        raise ValueError('dataset_path is required')
    return train(dataset_path, limit=payload.get('limit'), output_dir=payload.get('output_dir'))


@app.post('/infer')
def infer(payload: dict) -> dict:
    return predict(payload)
from services.flow_forecast_service.logic import SERVICE_DEFINITION, predict
from shared.service_base import create_inference_app

app = create_inference_app(SERVICE_DEFINITION.service_name, predict)

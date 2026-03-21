from __future__ import annotations

from pathlib import Path
from fastapi.testclient import TestClient
from services.flow_anomaly_service.app import app as anomaly_app
from services.flow_forecast_service.app import app as forecast_app
from shared.config.settings import get_settings
from shared.schemas.common import BuildTasksRequest, ReplayRequest
from system_services.data_replay_service.app import app as replay_app
from system_services.window_builder_service.app import app as builder_app
from training.flow_anomaly.train import train as train_anomaly
from training.flow_forecast.train import train as train_forecast

DATASET = 'dataset/node_1.csv'


def ensure_models():
    settings = get_settings()
    anomaly_model = settings.models_dir / 'flow_anomaly_service.joblib'
    forecast_model = settings.models_dir / 'flow_forecast_service.joblib'
    if not anomaly_model.exists():
        train_anomaly(DATASET)
    if not forecast_model.exists():
        train_forecast(DATASET)


def test_replay_and_window_build_pipeline():
    replay_client = TestClient(replay_app)
    builder_client = TestClient(builder_app)
    replay_resp = replay_client.post('/replay', json=ReplayRequest(dataset_path=DATASET, limit=30).model_dump())
    assert replay_resp.status_code == 200
    records = replay_resp.json()['records']
    assert len(records) == 30

    build_resp = builder_client.post('/build', json=BuildTasksRequest(
        records=records,
        source_edge_node='edge-node-test',
        target_services=['flow_anomaly_service', 'flow_forecast_service'],
    ).model_dump(mode='json'))
    assert build_resp.status_code == 200
    payload = build_resp.json()
    assert any(task['service_name'] == 'flow_anomaly_service' for task in payload['generated_tasks'])
    assert any(task['service_name'] == 'flow_forecast_service' for task in payload['generated_tasks'])


def test_inference_services_return_unified_schema():
    ensure_models()
    replay_client = TestClient(replay_app)
    builder_client = TestClient(builder_app)
    anomaly_client = TestClient(anomaly_app)
    forecast_client = TestClient(forecast_app)

    records = replay_client.post('/replay', json=ReplayRequest(dataset_path=DATASET, limit=30).model_dump()).json()['records']
    tasks = builder_client.post('/build', json=BuildTasksRequest(
        records=records,
        source_edge_node='edge-node-test',
        target_services=['flow_anomaly_service', 'flow_forecast_service'],
    ).model_dump(mode='json')).json()['generated_tasks']

    anomaly_task = next(task for task in tasks if task['service_name'] == 'flow_anomaly_service')
    forecast_task = next(task for task in tasks if task['service_name'] == 'flow_forecast_service')

    anomaly_resp = anomaly_client.post('/infer', json=anomaly_task)
    assert anomaly_resp.status_code == 200
    assert anomaly_resp.json()['result_type'] == 'anomaly'

    forecast_resp = forecast_client.post('/infer', json=forecast_task)
    assert forecast_resp.status_code == 200
    assert forecast_resp.json()['result_type'] == 'forecast'

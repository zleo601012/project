from __future__ import annotations

import csv
from pathlib import Path

from fastapi.testclient import TestClient

from services.flow_anomaly_service.app import app as anomaly_app
from services.flow_forecast_service.app import app as forecast_app
from services.flow_anomaly_service.logic import SERVICE_DEFINITION as ANOMALY_DEFINITION
from services.flow_forecast_service.logic import SERVICE_DEFINITION as FORECAST_DEFINITION

DATASET = 'dataset/node_1.csv'
_REQUIRED_FIELDS = ['ts', 'slot', 'node_id', 'flow_m3s', 'rain_intensity_mmph', 'temp_C']


def _load_rows(dataset_path: str, limit: int | None = None) -> list[dict[str, str]]:
    with Path(dataset_path).open('r', encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        rows = []
        for index, row in enumerate(reader):
            rows.append({key.lstrip('\ufeff'): value for key, value in row.items()})
            if limit is not None and index + 1 >= limit:
                break
    return rows


def _build_request(rows: list[dict[str, str]], service_name: str, window_length: int) -> dict:
    window = rows[:window_length]
    features = {field: [row[field] for row in window] for field in _REQUIRED_FIELDS}
    return {
        'task_id': f'{service_name}-test-1',
        'service_name': service_name,
        'source_edge_node': 'standalone-edge-node',
        'source_data_node': window[-1]['node_id'],
        'window_start': window[0]['ts'],
        'window_end': window[-1]['ts'],
        'deadline_ms': 3000,
        'features': features,
    }


def test_standalone_train_and_infer_for_flow_anomaly_service():
    client = TestClient(anomaly_app)
    train_response = client.post('/train', json={'dataset_path': DATASET, 'limit': 80})
    assert train_response.status_code == 200

    meta_response = client.get('/meta')
    assert meta_response.status_code == 200
    assert meta_response.json()['service_name'] == ANOMALY_DEFINITION.service_name
    assert meta_response.json()['model_ready'] is True

    infer_response = client.post(
        '/infer',
        json=_build_request(_load_rows(DATASET, limit=ANOMALY_DEFINITION.window_length), ANOMALY_DEFINITION.service_name, ANOMALY_DEFINITION.window_length),
    )
    assert infer_response.status_code == 200
    assert infer_response.json()['result_type'] == 'anomaly'
    assert infer_response.json()['model_version'] == ANOMALY_DEFINITION.model_version


def test_standalone_train_and_infer_for_flow_forecast_service():
    client = TestClient(forecast_app)
    train_response = client.post('/train', json={'dataset_path': DATASET, 'limit': 80})
    assert train_response.status_code == 200

    meta_response = client.get('/meta')
    assert meta_response.status_code == 200
    assert meta_response.json()['service_name'] == FORECAST_DEFINITION.service_name
    assert meta_response.json()['model_ready'] is True

    infer_response = client.post(
        '/infer',
        json=_build_request(_load_rows(DATASET, limit=FORECAST_DEFINITION.window_length), FORECAST_DEFINITION.service_name, FORECAST_DEFINITION.window_length),
    )
    assert infer_response.status_code == 200
    assert infer_response.json()['result_type'] == 'forecast'
    assert infer_response.json()['model_version'] == FORECAST_DEFINITION.model_version
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

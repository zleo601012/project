from __future__ import annotations

import importlib
from fastapi.testclient import TestClient
from shared.config.service_catalog import SERVICE_CATALOG
from shared.config.settings import get_settings
from shared.schemas.common import BuildTasksRequest, ReplayRequest
from system_services.data_replay_service.app import app as replay_app
from system_services.window_builder_service.app import app as builder_app
from shared.ml.training import train_service

DATASET = 'dataset/node_1.csv'
TRAIN_LIMIT = 160
REPLAY_LIMIT = 80


def ensure_models():
    settings = get_settings()
    for service_name in SERVICE_CATALOG:
        model_path = settings.models_dir / f'{service_name}.joblib'
        if not model_path.exists():
            train_service(service_name, DATASET, limit=TRAIN_LIMIT)


def _client(service_name: str) -> TestClient:
    module = importlib.import_module(f'services.{service_name}.app')
    return TestClient(module.app)


def test_window_builder_generates_all_services():
    replay_client = TestClient(replay_app)
    builder_client = TestClient(builder_app)
    records = replay_client.post('/replay', json=ReplayRequest(dataset_path=DATASET, limit=REPLAY_LIMIT).model_dump()).json()['records']
    response = builder_client.post('/build', json=BuildTasksRequest(
        records=records,
        source_edge_node='edge-node-test',
        target_services=list(SERVICE_CATALOG.keys()),
    ).model_dump(mode='json'))
    assert response.status_code == 200
    tasks = response.json()['generated_tasks']
    generated_names = {task['service_name'] for task in tasks}
    assert generated_names == set(SERVICE_CATALOG.keys())


def test_all_service_endpoints_can_infer():
    ensure_models()
    replay_client = TestClient(replay_app)
    builder_client = TestClient(builder_app)
    records = replay_client.post('/replay', json=ReplayRequest(dataset_path=DATASET, limit=REPLAY_LIMIT).model_dump()).json()['records']
    tasks = builder_client.post('/build', json=BuildTasksRequest(
        records=records,
        source_edge_node='edge-node-test',
        target_services=list(SERVICE_CATALOG.keys()),
    ).model_dump(mode='json')).json()['generated_tasks']

    first_task_per_service = {}
    for task in tasks:
        first_task_per_service.setdefault(task['service_name'], task)

    for service_name, definition in SERVICE_CATALOG.items():
        response = _client(service_name).post('/infer', json=first_task_per_service[service_name])
        assert response.status_code == 200
        payload = response.json()
        assert payload['service_name'] == service_name
        assert payload['model_version'] == definition.model_version
        if definition.task_type == 'anomaly':
            assert payload['result_type'] == 'anomaly'
            assert 'score' in payload
        elif definition.task_type == 'forecast':
            assert payload['result_type'] == 'forecast'
            assert 'prediction' in payload
        else:
            assert payload['result_type'] == 'risk_score'
            assert 'risk_score' in payload

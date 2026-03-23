from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from services.flow_anomaly_service.app import app as anomaly_app
from services.flow_anomaly_service.logic import SERVICE_DEFINITION as ANOMALY_DEFINITION
from services.flow_forecast_service.app import app as forecast_app
from services.flow_forecast_service.logic import SERVICE_DEFINITION as FORECAST_DEFINITION
from shared.config.settings import get_settings
from shared.schemas.common import BuildTasksRequest, ReplayRequest
from system_services.data_replay_service.app import app as replay_app
from system_services.window_builder_service.app import app as builder_app
from training.flow_anomaly.train import train as train_anomaly
from training.flow_forecast.train import train as train_forecast

DATASET_DEFAULT = 'dataset/node_1.csv'
TARGET_SERVICES = ['flow_anomaly_service', 'flow_forecast_service']


def _metadata_path(service_name: str) -> Path:
    return get_settings().models_dir / f'{service_name}.metadata.json'


def _metadata_matches(service_name: str, expected_version: str, expected_model_name: str) -> bool:
    metadata_path = _metadata_path(service_name)
    if not metadata_path.exists():
        return False
    try:
        metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
    except json.JSONDecodeError:
        return False
    return (
        metadata.get('model_version') == expected_version
        and metadata.get('model_name') == expected_model_name
    )


def ensure_models(dataset_path: str, limit: int | None = None) -> None:
    settings = get_settings()
    required = {
        'flow_anomaly_service': settings.models_dir / 'flow_anomaly_service.joblib',
        'flow_forecast_service': settings.models_dir / 'flow_forecast_service.joblib',
    }
    if (
        not required['flow_anomaly_service'].exists()
        or not _metadata_matches(
            'flow_anomaly_service',
            ANOMALY_DEFINITION.model_version,
            ANOMALY_DEFINITION.model_name,
        )
    ):
        print(f'[train] flow_anomaly_service <- {dataset_path}')
        train_anomaly(dataset_path, limit=limit)
    if (
        not required['flow_forecast_service'].exists()
        or not _metadata_matches(
            'flow_forecast_service',
            FORECAST_DEFINITION.model_version,
            FORECAST_DEFINITION.model_name,
        )
    ):
        print(f'[train] flow_forecast_service <- {dataset_path}')
        train_forecast(dataset_path, limit=limit)


def build_tasks(dataset_path: str, limit: int) -> list[dict]:
    settings = get_settings()
    replay_client = TestClient(replay_app)
    builder_client = TestClient(builder_app)
    replay_resp = replay_client.post('/replay', json=ReplayRequest(dataset_path=dataset_path, limit=limit).model_dump())
    if replay_resp.status_code != 200:
        raise SystemExit(f'replay failed: {replay_resp.json()}')
    records = replay_resp.json()['records']
    build_resp = builder_client.post('/build', json=BuildTasksRequest(
        records=records,
        source_edge_node=settings.default_edge_node_id,
        target_services=TARGET_SERVICES,
        deadline_ms=settings.default_deadline_ms,
    ).model_dump(mode='json'))
    if build_resp.status_code != 200:
        raise SystemExit(f'build failed: {build_resp.json()}')
    tasks = build_resp.json()['generated_tasks']
    print(f'[build] replay_records={len(records)} generated_tasks={len(tasks)}')
    return tasks


def check_service(name: str, app, task: dict) -> None:
    client = TestClient(app)
    health = client.get('/health')
    meta = client.get('/meta')
    infer = client.post('/infer', json=task)
    print(f'[{name}] health={health.status_code} {json.dumps(health.json(), ensure_ascii=False)}')
    print(f'[{name}] meta={meta.status_code} {json.dumps(meta.json(), ensure_ascii=False)}')
    print(f'[{name}] infer={infer.status_code} {json.dumps(infer.json(), ensure_ascii=False)}')
    if health.status_code != 200:
        raise SystemExit(f'{name} health failed')
    if meta.status_code != 200:
        raise SystemExit(f'{name} meta failed')
    if infer.status_code != 200:
        raise SystemExit(f'{name} infer failed')


def main() -> None:
    parser = argparse.ArgumentParser(description='Smoke-test flow anomaly and flow forecast services without uvicorn or pytest.')
    parser.add_argument('--dataset', default=DATASET_DEFAULT)
    parser.add_argument('--limit', type=int, default=80)
    parser.add_argument('--train-limit', type=int, default=None)
    args = parser.parse_args()

    ensure_models(args.dataset, limit=args.train_limit)
    tasks = build_tasks(args.dataset, limit=args.limit)
    anomaly_task = next(task for task in tasks if task['service_name'] == 'flow_anomaly_service')
    forecast_task = next(task for task in tasks if task['service_name'] == 'flow_forecast_service')
    check_service('flow_anomaly_service', anomaly_app, anomaly_task)
    check_service('flow_forecast_service', forecast_app, forecast_task)
    print('flow services smoke test passed')


if __name__ == '__main__':
    main()

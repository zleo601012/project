from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from services.flow_anomaly_service.app import app as anomaly_app
from services.flow_forecast_service.app import app as forecast_app
from services.flow_anomaly_service.logic import SERVICE_DEFINITION as ANOMALY_DEFINITION
from services.flow_forecast_service.logic import SERVICE_DEFINITION as FORECAST_DEFINITION

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
    if len(rows) < window_length:
        raise SystemExit(f'not enough records for {service_name}; need at least {window_length}, got {len(rows)}')
    window = rows[:window_length]
    features = {field: [row[field] for row in window] for field in _REQUIRED_FIELDS}
    return {
        'task_id': f'{service_name}-smoke-1',
        'service_name': service_name,
        'source_edge_node': 'standalone-edge-node',
        'source_data_node': window[-1]['node_id'],
        'window_start': window[0]['ts'],
        'window_end': window[-1]['ts'],
        'deadline_ms': 3000,
        'features': features,
    }


def _exercise_service(client: TestClient, service_name: str, dataset_path: str, limit: int, window_length: int) -> None:
    health = client.get('/health')
    train = client.post('/train', json={'dataset_path': dataset_path, 'limit': limit})
    meta = client.get('/meta')
    infer = client.post('/infer', json=_build_request(_load_rows(dataset_path, limit=limit), service_name, window_length))
    print(f'[{service_name}] health={health.status_code} {json.dumps(health.json(), ensure_ascii=False)}')
    print(f'[{service_name}] train={train.status_code} {json.dumps(train.json(), ensure_ascii=False)}')
    print(f'[{service_name}] meta={meta.status_code} {json.dumps(meta.json(), ensure_ascii=False)}')
    print(f'[{service_name}] infer={infer.status_code} {json.dumps(infer.json(), ensure_ascii=False)}')
    if health.status_code != 200 or train.status_code != 200 or meta.status_code != 200 or infer.status_code != 200:
        raise SystemExit(f'{service_name} smoke test failed')


def main() -> None:
    parser = argparse.ArgumentParser(description='Smoke-test the standalone flow anomaly and flow forecast services.')
    parser.add_argument('--dataset', default='dataset/node_1.csv')
    parser.add_argument('--limit', type=int, default=80)
    args = parser.parse_args()

    _exercise_service(TestClient(anomaly_app), ANOMALY_DEFINITION.service_name, args.dataset, args.limit, ANOMALY_DEFINITION.window_length)
    _exercise_service(TestClient(forecast_app), FORECAST_DEFINITION.service_name, args.dataset, args.limit, FORECAST_DEFINITION.window_length)
    print('flow standalone services smoke test passed')
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


def _find_task(tasks: list[dict], service_name: str, replay_limit: int) -> dict:
    for task in tasks:
        if task['service_name'] == service_name:
            return task
    raise SystemExit(
        f'no task generated for {service_name}; increase --limit (current: {replay_limit}) '
        'so the window builder has enough records.'
    )


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
    anomaly_task = _find_task(tasks, 'flow_anomaly_service', args.limit)
    forecast_task = _find_task(tasks, 'flow_forecast_service', args.limit)
    anomaly_task = next(task for task in tasks if task['service_name'] == 'flow_anomaly_service')
    forecast_task = next(task for task in tasks if task['service_name'] == 'flow_forecast_service')
    check_service('flow_anomaly_service', anomaly_app, anomaly_task)
    check_service('flow_forecast_service', forecast_app, forecast_task)
    print('flow services smoke test passed')


if __name__ == '__main__':
    main()

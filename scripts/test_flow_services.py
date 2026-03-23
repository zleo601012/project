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


if __name__ == '__main__':
    main()

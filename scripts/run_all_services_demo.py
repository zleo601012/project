from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from shared.config.service_catalog import SERVICE_CATALOG
from shared.config.settings import get_settings
from shared.schemas.common import BuildTasksRequest, ReplayRequest
from system_services.data_replay_service.app import app as replay_app
from system_services.window_builder_service.app import app as builder_app


def _service_client(service_name: str) -> TestClient:
    module = importlib.import_module(f'services.{service_name}.app')
    return TestClient(module.app)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', required=True)
    parser.add_argument('--limit', type=int, default=80)
    args = parser.parse_args()

    settings = get_settings()
    missing = [
        service_name
        for service_name in SERVICE_CATALOG
        if not (settings.models_dir / f'{service_name}.joblib').exists()
    ]
    if missing:
        raise SystemExit(f'缺少模型文件，请先运行训练脚本。missing={missing}')

    replay_client = TestClient(replay_app)
    builder_client = TestClient(builder_app)
    replay_resp = replay_client.post('/replay', json=ReplayRequest(dataset_path=args.dataset, limit=args.limit).model_dump())
    records = replay_resp.json()['records']
    build_resp = builder_client.post('/build', json=BuildTasksRequest(
        records=records,
        source_edge_node=settings.default_edge_node_id,
        target_services=list(SERVICE_CATALOG.keys()),
        deadline_ms=settings.default_deadline_ms,
    ).model_dump(mode='json'))
    tasks = build_resp.json()['generated_tasks']
    print(f'replay records={len(records)} generated_tasks={len(tasks)} services={len(SERVICE_CATALOG)}')

    by_service = {}
    for task in tasks:
        by_service.setdefault(task['service_name'], task)

    for service_name in SERVICE_CATALOG:
        client = _service_client(service_name)
        response = client.post('/infer', json=by_service[service_name])
        print(service_name, response.json())


if __name__ == '__main__':
    main()

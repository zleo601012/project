from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from services.flow_anomaly_service.app import app as anomaly_app
from services.flow_forecast_service.app import app as forecast_app
from shared.config.settings import get_settings
from shared.schemas.common import BuildTasksRequest, ReplayRequest
from system_services.data_replay_service.app import app as replay_app
from system_services.window_builder_service.app import app as builder_app


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', required=True)
    parser.add_argument('--limit', type=int, default=80)
    args = parser.parse_args()

    settings = get_settings()
    required_models = [
        settings.models_dir / 'flow_anomaly_service.joblib',
        settings.models_dir / 'flow_forecast_service.joblib',
    ]
    if not all(path.exists() for path in required_models):
        raise SystemExit('请先运行 python scripts/train_phase1_models.py --dataset <path> 训练阶段1模型。')

    replay_client = TestClient(replay_app)
    builder_client = TestClient(builder_app)
    anomaly_client = TestClient(anomaly_app)
    forecast_client = TestClient(forecast_app)

    replay_resp = replay_client.post('/replay', json=ReplayRequest(dataset_path=args.dataset, limit=args.limit).model_dump())
    records = replay_resp.json()['records']
    task_resp = builder_client.post('/build', json=BuildTasksRequest(
        records=records,
        source_edge_node=settings.default_edge_node_id,
        target_services=['flow_anomaly_service', 'flow_forecast_service'],
        deadline_ms=settings.default_deadline_ms,
    ).model_dump(mode='json'))
    tasks = task_resp.json()['generated_tasks']

    print(f'replay records={len(records)} generated_tasks={len(tasks)}')
    for task in tasks:
        if task['service_name'] == 'flow_anomaly_service':
            print(anomaly_client.post('/infer', json=task).json())
            break
    for task in tasks:
        if task['service_name'] == 'flow_forecast_service':
            print(forecast_client.post('/infer', json=task).json())
            break


if __name__ == '__main__':
    main()

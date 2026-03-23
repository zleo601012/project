from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from fastapi.testclient import TestClient

from shared.config.service_catalog import SERVICE_CATALOG
from shared.config.settings import get_settings
from shared.schemas.common import BuildTasksRequest, ReplayRequest
from system_services.data_replay_service.app import app as replay_app
from system_services.window_builder_service.app import app as builder_app
from training.flow_anomaly.train import train as train_flow_anomaly

DATASET = 'dataset/node_1.csv'


def _pick_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def _wait_until_ready(base_url: str, timeout_seconds: float = 10.0) -> dict:
    deadline = time.time() + timeout_seconds
    last_error = None
    while time.time() < deadline:
        try:
            with urlopen(f'{base_url}/health', timeout=1.0) as response:
                return json.loads(response.read().decode('utf-8'))
        except URLError as exc:
            last_error = exc
            time.sleep(0.1)
    raise AssertionError(f'service did not become ready: {last_error}')


def _request_json(url: str, payload: dict) -> dict:
    request = Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    with urlopen(request, timeout=5.0) as response:
        return json.loads(response.read().decode('utf-8'))


def test_every_service_has_container_assets():
    for service_name in SERVICE_CATALOG:
        service_dir = Path('services') / service_name
        assert (service_dir / 'Dockerfile').exists(), f'missing Dockerfile for {service_name}'
        assert (service_dir / 'server.py').exists(), f'missing server.py for {service_name}'


def test_flow_anomaly_service_can_run_over_http():
    settings = get_settings()
    model_path = settings.models_dir / 'flow_anomaly_service.joblib'
    if not model_path.exists():
        train_flow_anomaly(DATASET)

    replay_client = TestClient(replay_app)
    builder_client = TestClient(builder_app)
    records = replay_client.post('/replay', json=ReplayRequest(dataset_path=DATASET, limit=30).model_dump()).json()['records']
    tasks = builder_client.post('/build', json=BuildTasksRequest(
        records=records,
        source_edge_node='edge-node-test',
        target_services=['flow_anomaly_service'],
    ).model_dump(mode='json')).json()['generated_tasks']
    task_payload = tasks[0]

    port = _pick_port()
    env = os.environ.copy()
    env['PORT'] = str(port)
    process = subprocess.Popen(
        [sys.executable, '-m', 'services.flow_anomaly_service.server'],
        cwd=Path.cwd(),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        health = _wait_until_ready(f'http://127.0.0.1:{port}')
        assert health['status'] == 'ok'
        assert health['service_name'] == 'flow_anomaly_service'

        payload = _request_json(f'http://127.0.0.1:{port}/infer', task_payload)
        assert payload['service_name'] == 'flow_anomaly_service'
        assert payload['result_type'] == 'anomaly'
        assert 'score' in payload
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)

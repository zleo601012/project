from __future__ import annotations

import time
from datetime import datetime, timezone
from fastapi import FastAPI
from shared.config.service_catalog import SERVICE_CATALOG
from shared.logging.json_logger import log_task
from shared.ml.model_io import load_metadata, load_model
from shared.schemas.common import (
    AnomalyResponse,
    ForecastResponse,
    InferRequest,
    RiskScoreResponse,
    ServiceMeta,
    TaskLogEntry,
)


def create_inference_app(service_name: str, predictor):
    definition = SERVICE_CATALOG[service_name]
    app = FastAPI(title=service_name)

    state: dict[str, object] = {}

    def ensure_loaded() -> tuple[object, dict]:
        if 'model' not in state:
            state['model'] = load_model(service_name)
            state['metadata'] = load_metadata(service_name)
        return state['model'], state['metadata']

    response_model = {
        'anomaly': AnomalyResponse,
        'forecast': ForecastResponse,
        'risk_score': RiskScoreResponse,
    }[definition.task_type]

    @app.get('/health')
    def health():
        return {'status': 'ok', 'service_name': service_name}

    @app.get('/meta', response_model=ServiceMeta)
    def meta():
        metadata = ensure_loaded()[1]
        return ServiceMeta(
            service_name=service_name,
            model_name=metadata['model_name'],
            model_version=metadata['model_version'],
            task_type=definition.task_type,
            window_length=definition.window_length,
            input_fields=definition.input_fields,
        )

    @app.post('/infer', response_model=response_model)
    def infer(request: InferRequest):
        submit_ts = datetime.now(timezone.utc)
        start = time.perf_counter()
        model, metadata = ensure_loaded()
        response = predictor(model, metadata, request)
        inference_ms = int((time.perf_counter() - start) * 1000)
        end_ts = datetime.now(timezone.utc)
        log_task(TaskLogEntry(
            task_id=request.task_id,
            service_name=request.service_name,
            source_edge_node=request.source_edge_node,
            target_edge_node=request.source_edge_node,
            source_data_node=request.source_data_node,
            window_start=request.window_start,
            window_end=request.window_end,
            submit_ts=submit_ts,
            start_ts=submit_ts,
            end_ts=end_ts,
            latency_ms=max(inference_ms, 1),
            queue_ms=0,
            inference_ms=inference_ms,
            status='success',
            decision_type='local_running_instance',
            image_ready=True,
            image_pull_used=False,
            container_cold_start_used=False,
            extra={'task_type': definition.task_type},
        ))
        response.inference_ms = inference_ms
        return response

    return app

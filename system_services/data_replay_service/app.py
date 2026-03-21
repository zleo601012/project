from __future__ import annotations

import time
from fastapi import FastAPI
from shared.config.settings import get_settings
from shared.schemas.common import ReplayRequest, ReplayResponse
from shared.utils.dataset import load_records

app = FastAPI(title='data_replay_service')

@app.get('/health')
def health():
    return {'status': 'ok', 'service_name': 'data_replay_service'}

@app.post('/replay', response_model=ReplayResponse)
def replay(request: ReplayRequest):
    settings = get_settings()
    records = load_records(request.dataset_path, limit=request.limit)
    if request.emit_sleep:
        for _ in records:
            time.sleep(settings.replay_interval_seconds / request.speedup)
    return ReplayResponse(dataset_path=request.dataset_path, emitted=len(records), records=records)

from __future__ import annotations

from fastapi import FastAPI
from shared.schemas.common import BuildTasksRequest, BuildTasksResponse
from shared.utils.windowing import build_tasks

app = FastAPI(title='window_builder_service')

@app.get('/health')
def health():
    return {'status': 'ok', 'service_name': 'window_builder_service'}

@app.post('/build', response_model=BuildTasksResponse)
def build(request: BuildTasksRequest):
    return build_tasks(request)

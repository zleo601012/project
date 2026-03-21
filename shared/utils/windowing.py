from __future__ import annotations

from collections import defaultdict, deque
from uuid import uuid4
from shared.config.service_catalog import ALL_DATA_FIELDS, SERVICE_CATALOG
from shared.schemas.common import BuildTasksRequest, BuildTasksResponse, FeatureWindow, InferRequest, ReplayRecord


def _record_value(record: ReplayRecord, field: str):
    return getattr(record, field)


def build_tasks(request: BuildTasksRequest) -> BuildTasksResponse:
    tasks: list[InferRequest] = []
    grouped: dict[str, list[ReplayRecord]] = defaultdict(list)
    for record in request.records:
        grouped[str(record.node_id)].append(record)

    for data_node, records in grouped.items():
        for service_name in request.target_services:
            definition = SERVICE_CATALOG[service_name]
            window = deque(maxlen=definition.window_length)
            for idx, record in enumerate(records):
                window.append(record)
                if len(window) < definition.window_length:
                    continue
                if idx % 2 != 1:
                    continue
                feature_payload = {
                    field: [_record_value(item, field) for item in window]
                    for field in ALL_DATA_FIELDS
                }
                tasks.append(
                    InferRequest(
                        task_id=f'{service_name}-{data_node}-{uuid4().hex[:8]}',
                        service_name=service_name,
                        source_edge_node=request.source_edge_node,
                        source_data_node=data_node,
                        window_start=window[0].ts,
                        window_end=window[-1].ts,
                        deadline_ms=request.deadline_ms,
                        features=FeatureWindow(**feature_payload),
                    )
                )
    return BuildTasksResponse(generated_tasks=tasks)

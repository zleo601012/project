from __future__ import annotations

import json
import logging
from shared.schemas.common import TaskLogEntry

logger = logging.getLogger('edge_offload')
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


def log_task(entry: TaskLogEntry) -> None:
    logger.info(json.dumps(entry.model_dump(mode='json'), ensure_ascii=False))

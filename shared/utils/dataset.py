from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable
from shared.schemas.common import ReplayRecord

FIELD_ALIASES = {'﻿ts': 'ts'}
FLOAT_FIELDS = {
    'rain_intensity_mmph', 'flow_m3s', 'temp_C', 'pH', 'DO_mgL', 'EC_uScm', 'COD_mgL',
    'NH3N_mgL', 'TN_mgL', 'TP_mgL', 'TSS_mgL', 'turbidity_NTU'
}
INT_FIELDS = {'slot'}
STR_FIELDS = {'ts', 'node_id'}


def _normalize(row: dict[str, str]) -> dict[str, object]:
    normalized: dict[str, object] = {}
    for key, value in row.items():
        key = FIELD_ALIASES.get(key, key)
        if key in FLOAT_FIELDS:
            normalized[key] = float(value)
        elif key in INT_FIELDS:
            normalized[key] = int(value)
        elif key in STR_FIELDS:
            normalized[key] = value
        else:
            normalized[key] = value
    return normalized


def load_records(dataset_path: str | Path, limit: int | None = None) -> list[ReplayRecord]:
    path = Path(dataset_path)
    with path.open(newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        rows = []
        for idx, row in enumerate(reader):
            rows.append(ReplayRecord(**_normalize(row)))
            if limit is not None and idx + 1 >= limit:
                break
    return rows


def iter_records(dataset_path: str | Path, limit: int | None = None) -> Iterable[ReplayRecord]:
    for row in load_records(dataset_path, limit=limit):
        yield row

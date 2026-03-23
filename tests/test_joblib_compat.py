from __future__ import annotations

import json
from pathlib import Path

import joblib


def test_joblib_load_supports_pickle_payload(tmp_path: Path) -> None:
    path = tmp_path / 'model.joblib'
    payload = {'kind': 'pickle', 'value': [1, 2, 3]}
    joblib.dump(payload, path)

    assert joblib.load(path) == payload


def test_joblib_load_supports_json_payload(tmp_path: Path) -> None:
    path = tmp_path / 'model.joblib'
    payload = {'kind': 'json', 'value': {'threshold': 0.82}}
    path.write_text(json.dumps(payload), encoding='utf-8')

    assert joblib.load(path) == payload

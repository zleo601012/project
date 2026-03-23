from __future__ import annotations

import py_compile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _flow_python_files() -> list[Path]:
    targets = [
        ROOT / 'scripts' / 'test_flow_services.py',
        *sorted((ROOT / 'services' / 'flow_anomaly_service').glob('*.py')),
        *sorted((ROOT / 'services' / 'flow_forecast_service').glob('*.py')),
    ]
    return targets


def test_flow_service_python_files_compile() -> None:
    for path in _flow_python_files():
        py_compile.compile(str(path), doraise=True)

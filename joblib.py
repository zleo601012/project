from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Any


def dump(obj: Any, filename) -> None:
    with open(filename, 'wb') as f:
        pickle.dump(obj, f)


def load(filename):
    path = Path(filename)
    with path.open('rb') as f:
        try:
            return pickle.load(f)
        except (pickle.UnpicklingError, EOFError, AttributeError, ValueError):
            f.seek(0)
            return json.loads(f.read().decode('utf-8'))

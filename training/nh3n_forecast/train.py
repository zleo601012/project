from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.nh3n_forecast_service.logic import train as service_train


def train(dataset_path: str, limit: int | None = None):
    return service_train(dataset_path, limit=limit)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', required=True)
    parser.add_argument('--limit', type=int, default=None)
    args = parser.parse_args()
    print(train(args.dataset, limit=args.limit))


if __name__ == '__main__':
    main()

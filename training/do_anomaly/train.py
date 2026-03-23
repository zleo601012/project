from __future__ import annotations

import argparse
from pathlib import Path
from shared.ml.training import train_service

SERVICE_NAME = 'do_anomaly_service'


def train(dataset_path: str | Path, limit: int | None = None) -> dict:
    return train_service(SERVICE_NAME, dataset_path, limit=limit)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', required=True)
    parser.add_argument('--limit', type=int, default=None)
    args = parser.parse_args()
    metadata = train(args.dataset, limit=args.limit)
    print(metadata)


if __name__ == '__main__':
    main()

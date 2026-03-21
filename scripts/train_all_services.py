from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.config.service_catalog import SERVICE_CATALOG
from shared.ml.training import train_service


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', required=True)
    parser.add_argument('--limit', type=int, default=None)
    args = parser.parse_args()

    for service_name in SERVICE_CATALOG:
        print(train_service(service_name, args.dataset, limit=args.limit))


if __name__ == '__main__':
    main()

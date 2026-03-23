from __future__ import annotations

import argparse

from services.flow_anomaly_service.logic import train as train_service


def main() -> None:
    parser = argparse.ArgumentParser(description='Train the standalone flow anomaly service.')
    parser.add_argument('--dataset', required=True)
    parser.add_argument('--limit', type=int, default=None)
    parser.add_argument('--output-dir', default=None)
    args = parser.parse_args()
    print(train_service(args.dataset, limit=args.limit, output_dir=args.output_dir))


if __name__ == '__main__':
    main()

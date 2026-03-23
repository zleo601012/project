from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from training.flow_anomaly.train import train as train_flow_anomaly
from training.flow_forecast.train import train as train_flow_forecast
from shared.ml.training import train_service

PHASE1_SERVICES = ['flow_anomaly_service', 'flow_forecast_service']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', required=True)
    parser.add_argument('--limit', type=int, default=None)
    args = parser.parse_args()
    print(train_flow_anomaly(args.dataset, limit=args.limit))
    print(train_flow_forecast(args.dataset, limit=args.limit))
    for service_name in PHASE1_SERVICES:
        print(train_service(service_name, args.dataset, limit=args.limit))


if __name__ == '__main__':
    main()

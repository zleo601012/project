from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from training.flow_anomaly.train import train as train_flow_anomaly
from training.flow_forecast.train import train as train_flow_forecast


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', required=True)
    args = parser.parse_args()
    print(train_flow_anomaly(args.dataset))
    print(train_flow_forecast(args.dataset))


if __name__ == '__main__':
    main()

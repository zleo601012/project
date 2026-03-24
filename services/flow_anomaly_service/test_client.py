from __future__ import annotations

import argparse
import json
import time
from typing import Any

import requests


DEFAULT_WINDOW = [
    {"flow_m3s": 1.2, "rain_intensity_mmph": 0.0, "temp_C": 23.1},
    {"flow_m3s": 1.3, "rain_intensity_mmph": 0.0, "temp_C": 23.0},
    {"flow_m3s": 1.4, "rain_intensity_mmph": 0.1, "temp_C": 22.9},
    {"flow_m3s": 1.3, "rain_intensity_mmph": 0.0, "temp_C": 23.1},
    {"flow_m3s": 1.2, "rain_intensity_mmph": 0.0, "temp_C": 23.0},
    {"flow_m3s": 1.1, "rain_intensity_mmph": 0.0, "temp_C": 22.9},
    {"flow_m3s": 1.0, "rain_intensity_mmph": 0.2, "temp_C": 22.8},
    {"flow_m3s": 1.2, "rain_intensity_mmph": 0.0, "temp_C": 22.9},
    {"flow_m3s": 1.3, "rain_intensity_mmph": 0.0, "temp_C": 23.0},
    {"flow_m3s": 1.4, "rain_intensity_mmph": 0.0, "temp_C": 23.1},
    {"flow_m3s": 1.5, "rain_intensity_mmph": 0.0, "temp_C": 23.2},
    {"flow_m3s": 1.6, "rain_intensity_mmph": 0.0, "temp_C": 23.3},
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Call /detect and print result + runtime")
    parser.add_argument("--url", default="http://127.0.0.1:8000/detect")
    parser.add_argument("--repeat", type=int, default=1, help="Number of requests to send")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload: dict[str, Any] = {"window": DEFAULT_WINDOW}

    all_ms: list[float] = []
    last_body: dict[str, Any] | None = None

    for i in range(args.repeat):
        start = time.perf_counter()
        response = requests.post(args.url, json=payload, timeout=10)
        elapsed_ms = (time.perf_counter() - start) * 1000
        all_ms.append(elapsed_ms)

        response.raise_for_status()
        last_body = response.json()
        print(f"request={i + 1}, runtime_ms={elapsed_ms:.2f}")

    if last_body is not None:
        print("result_json=")
        print(json.dumps(last_body, ensure_ascii=False, indent=2))

    avg_ms = sum(all_ms) / len(all_ms)
    print(f"avg_runtime_ms={avg_ms:.2f}")


if __name__ == "__main__":
    main()

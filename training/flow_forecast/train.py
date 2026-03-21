from __future__ import annotations

import argparse
from pathlib import Path
from lightgbm import LGBMRegressor
from shared.ml.feature_engineering import make_feature_vector
from shared.ml.model_io import save_model
from shared.schemas.common import BuildTasksRequest
from shared.utils.dataset import load_records
from shared.utils.windowing import build_tasks

SERVICE_NAME = 'flow_forecast_service'


def train(dataset_path: str | Path) -> dict:
    records = load_records(dataset_path)
    tasks = build_tasks(BuildTasksRequest(
        records=records,
        source_edge_node='trainer',
        target_services=[SERVICE_NAME],
        deadline_ms=3000,
    )).generated_tasks
    features = [make_feature_vector(task) for task in tasks[:-1]]
    targets = [task.features.flow_m3s[-1] for task in tasks[1:]]
    usable = min(len(features), len(targets))
    features = features[:usable]
    targets = targets[:usable]
    model = LGBMRegressor(random_state=42, n_estimators=50, learning_rate=0.1, max_depth=4)
    model.fit(features, targets)
    metadata = {
        'service_name': SERVICE_NAME,
        'model_name': 'LightGBMRegressor',
        'model_version': 'v1',
        'training_samples': len(features),
        'dataset_path': str(dataset_path),
    }
    save_model(SERVICE_NAME, model, metadata)
    return metadata


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', required=True)
    args = parser.parse_args()
    metadata = train(args.dataset)
    print(metadata)


if __name__ == '__main__':
    main()

from __future__ import annotations

import argparse
from pathlib import Path
from sklearn.ensemble import IsolationForest
from shared.ml.feature_engineering import make_feature_vector
from shared.ml.model_io import save_model
from shared.schemas.common import BuildTasksRequest
from shared.utils.dataset import load_records
from shared.utils.windowing import build_tasks

SERVICE_NAME = 'flow_anomaly_service'


def train(dataset_path: str | Path) -> dict:
    records = load_records(dataset_path)
    tasks = build_tasks(BuildTasksRequest(
        records=records,
        source_edge_node='trainer',
        target_services=[SERVICE_NAME],
        deadline_ms=3000,
    )).generated_tasks
    vectors = [make_feature_vector(task) for task in tasks]
    model = IsolationForest(random_state=42, contamination=0.1)
    model.fit(vectors)
    scores = [-float(score) for score in model.score_samples(vectors)]
    threshold = sorted(scores)[max(int(0.9 * len(scores)) - 1, 0)]
    metadata = {
        'service_name': SERVICE_NAME,
        'model_name': 'IsolationForest',
        'model_version': 'v1',
        'threshold': threshold,
        'training_samples': len(vectors),
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

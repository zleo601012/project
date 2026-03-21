from __future__ import annotations

from math import exp, sqrt

class XGBClassifier:
    def __init__(self, random_state=None):
        self.random_state = random_state
        self.pos_center = []
        self.neg_center = []
        self.base_rate = 0.5

    def fit(self, X, y):
        positives = [row for row, label in zip(X, y) if label == 1]
        negatives = [row for row, label in zip(X, y) if label == 0]
        cols = len(X[0]) if X else 0
        self.base_rate = sum(y) / len(y) if y else 0.5
        self.pos_center = [sum(row[i] for row in positives) / len(positives) for i in range(cols)] if positives else [0.0] * cols
        self.neg_center = [sum(row[i] for row in negatives) / len(negatives) for i in range(cols)] if negatives else [0.0] * cols
        return self

    def _distance(self, row, center):
        return sqrt(sum((row[i] - center[i]) ** 2 for i in range(len(row))))

    def predict_proba(self, X):
        outputs = []
        for row in X:
            pos = self._distance(row, self.pos_center)
            neg = self._distance(row, self.neg_center)
            margin = neg - pos
            probability = 1.0 / (1.0 + exp(-margin / max(len(row), 1)))
            probability = (probability + self.base_rate) / 2.0
            outputs.append([1.0 - probability, probability])
        return outputs

    def predict(self, X):
        return [1 if probs[1] >= 0.5 else 0 for probs in self.predict_proba(X)]

class XGBRegressor:
    def __init__(self, random_state=None):
        self.random_state = random_state
        self.mean_target = 0.0

    def fit(self, X, y):
        self.mean_target = sum(y) / len(y) if y else 0.0
        return self

    def predict(self, X):
        return [self.mean_target for _ in X]

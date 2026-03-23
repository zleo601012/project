from __future__ import annotations
from math import sqrt

class IsolationForest:
    def __init__(self, random_state=None, contamination=0.1):
        self.random_state = random_state
        self.contamination = contamination
        self.center = []

    def fit(self, X):
        if not X:
            raise ValueError('X must not be empty')
        cols = len(X[0])
        self.center = [sum(row[i] for row in X) / len(X) for i in range(cols)]
        return self

    def score_samples(self, X):
        scores = []
        for row in X:
            dist = sqrt(sum((row[i] - self.center[i]) ** 2 for i in range(len(row))))
            scores.append(-dist)
        return scores

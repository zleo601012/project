from __future__ import annotations

class LGBMRegressor:
    def __init__(self, random_state=None, n_estimators=100, learning_rate=0.1, max_depth=-1):
        self.random_state = random_state
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.max_depth = max_depth
        self.mean_target = 0.0

    def fit(self, X, y):
        if not y:
            raise ValueError('y must not be empty')
        self.mean_target = sum(y) / len(y)
        return self

    def predict(self, X):
        return [self.mean_target for _ in X]

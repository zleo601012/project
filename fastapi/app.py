from __future__ import annotations

class FastAPI:
    def __init__(self, title='app'):
        self.title = title
        self.routes = {}

    def get(self, path, response_model=None):
        def decorator(func):
            self.routes[('GET', path)] = func
            return func
        return decorator

    def post(self, path, response_model=None):
        def decorator(func):
            self.routes[('POST', path)] = func
            return func
        return decorator

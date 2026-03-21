from __future__ import annotations

import inspect
import typing

class Response:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload

class TestClient:
    __test__ = False
    def __init__(self, app):
        self.app = app

    def get(self, path):
        return self._call('GET', path, None)

    def post(self, path, json=None):
        return self._call('POST', path, json)

    def _call(self, method, path, payload):
        func = self.app.routes[(method, path)]
        sig = inspect.signature(func)
        hints = typing.get_type_hints(func)
        params = list(sig.parameters.values())
        try:
            if params:
                annotation = hints.get(params[0].name, params[0].annotation)
                arg = annotation(**payload) if annotation is not inspect._empty else payload
                result = func(arg)
            else:
                result = func()
            if hasattr(result, 'model_dump'):
                result = result.model_dump(mode='json')
            return Response(200, result)
        except Exception as exc:
            return Response(500, {'detail': str(exc)})

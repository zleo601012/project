from __future__ import annotations

import inspect
import json
import os
import typing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

_JSON_HEADERS = {'Content-Type': 'application/json; charset=utf-8'}


def _serialize(result):
    if hasattr(result, 'model_dump'):
        return result.model_dump(mode='json')
    return result


def _coerce_argument(func, payload):
    sig = inspect.signature(func)
    hints = typing.get_type_hints(func)
    params = list(sig.parameters.values())
    if not params:
        return ()
    annotation = hints.get(params[0].name, params[0].annotation)
    if annotation is inspect._empty:
        return (payload,)
    return (annotation(**payload),)


def _handler(app):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self._dispatch('GET')

        def do_POST(self):
            self._dispatch('POST')

        def log_message(self, format, *args):  # noqa: A003
            return

        def _dispatch(self, method: str):
            route = (method, urlparse(self.path).path)
            func = app.routes.get(route)
            if func is None:
                self._send(404, {'detail': f'Route not found: {route[1]}'})
                return

            try:
                payload = self._read_json() if method == 'POST' else None
                args = _coerce_argument(func, payload)
                result = _serialize(func(*args))
                self._send(200, result)
            except Exception as exc:  # pragma: no cover - surfaced to client for debugging
                self._send(500, {'detail': str(exc)})

        def _read_json(self):
            length = int(self.headers.get('Content-Length', '0'))
            if length <= 0:
                return {}
            body = self.rfile.read(length).decode('utf-8')
            return json.loads(body)

        def _send(self, status: int, payload):
            data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            self.send_response(status)
            for key, value in _JSON_HEADERS.items():
                self.send_header(key, value)
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    return Handler


def serve(app, service_name: str, host: str = '0.0.0.0', port: int | None = None) -> None:
    bind_port = port or int(os.environ.get('PORT', '8000'))
    server = ThreadingHTTPServer((host, bind_port), _handler(app))
    print(f'{service_name} listening on http://{host}:{bind_port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:  # pragma: no cover - manual shutdown path
        pass
    finally:
        server.server_close()

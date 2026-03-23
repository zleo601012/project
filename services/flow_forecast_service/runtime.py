from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse


class App:
    def __init__(self, title: str):
        self.title = title
        self.routes: dict[tuple[str, str], object] = {}

    def get(self, path: str):
        def decorator(func):
            self.routes[('GET', path)] = func
            return func
        return decorator

    def post(self, path: str):
        def decorator(func):
            self.routes[('POST', path)] = func
            return func
        return decorator


def serve(app: App, service_name: str, host: str = '0.0.0.0', port: int | None = None) -> None:
    bind_port = port or int(os.environ.get('PORT', '8000'))

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self._dispatch('GET')

        def do_POST(self):
            self._dispatch('POST')

        def log_message(self, format, *args):  # noqa: A003
            return

        def _dispatch(self, method: str) -> None:
            route = (method, urlparse(self.path).path)
            func = app.routes.get(route)
            if func is None:
                self._send(404, {'detail': f'Route not found: {route[1]}'})
                return

            try:
                payload = self._read_json() if method == 'POST' else None
                result = func(payload) if payload is not None else func()
                self._send(200, result)
            except Exception as exc:  # pragma: no cover
                self._send(500, {'detail': str(exc)})

        def _read_json(self) -> dict:
            length = int(self.headers.get('Content-Length', '0'))
            if length <= 0:
                return {}
            return json.loads(self.rfile.read(length).decode('utf-8'))

        def _send(self, status: int, payload: dict) -> None:
            data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    server = ThreadingHTTPServer((host, bind_port), Handler)
    print(f'{service_name} listening on http://{host}:{bind_port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:  # pragma: no cover
        pass
    finally:
        server.server_close()

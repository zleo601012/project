from __future__ import annotations

from .app import app
from .logic import SERVICE_DEFINITION
from .runtime import serve

if __name__ == '__main__':
    serve(app, service_name=SERVICE_DEFINITION.service_name)

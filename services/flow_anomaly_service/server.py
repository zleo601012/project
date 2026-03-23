from __future__ import annotations

from services.flow_anomaly_service.app import app
from shared.http_runtime import serve

if __name__ == '__main__':
    serve(app, service_name='flow_anomaly_service')

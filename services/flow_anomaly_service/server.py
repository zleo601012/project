from __future__ import annotations

from services.flow_anomaly_service.app import app
from services.flow_anomaly_service.logic import SERVICE_DEFINITION
from services.flow_anomaly_service.runtime import serve

if __name__ == '__main__':
    serve(app, service_name=SERVICE_DEFINITION.service_name)

from __future__ import annotations

from services.nh3n_forecast_service.app import app
from shared.http_runtime import serve

if __name__ == '__main__':
    serve(app, service_name='nh3n_forecast_service')

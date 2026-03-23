from __future__ import annotations

from services.mixed_sewage_rain_score_service.app import app
from shared.http_runtime import serve

if __name__ == '__main__':
    serve(app, service_name='mixed_sewage_rain_score_service')

"""flow_anomaly_service application package.

Expose `app` at package level for compatibility with legacy
`python -m services.flow_anomaly_service.server` launcher.
"""

from .main import app

__all__ = ["app"]
"""flow_anomaly_service application package."""

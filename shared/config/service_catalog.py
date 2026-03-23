from __future__ import annotations

from importlib import import_module

from shared.config.data_fields import ALL_DATA_FIELDS
from shared.config.service_definition import ServiceDefinition, TaskType

SERVICE_MODULES = [
    'flow_anomaly_service',
    'water_quality_anomaly_service',
    'cod_anomaly_service',
    'nh3n_anomaly_service',
    'tss_turbidity_anomaly_service',
    'do_anomaly_service',
    'flow_forecast_service',
    'cod_forecast_service',
    'nh3n_forecast_service',
    'tss_turbidity_forecast_service',
    'mixed_sewage_rain_score_service',
    'illegal_discharge_score_service',
]


def _load_definition(service_module: str) -> ServiceDefinition:
    module = import_module(f'services.{service_module}.logic')
    return module.SERVICE_DEFINITION


SERVICE_CATALOG: dict[str, ServiceDefinition] = {
    definition.service_name: definition
    for definition in (_load_definition(service_module) for service_module in SERVICE_MODULES)
}

ANOMALY_SERVICES = [name for name, item in SERVICE_CATALOG.items() if item.task_type == 'anomaly']
FORECAST_SERVICES = [name for name, item in SERVICE_CATALOG.items() if item.task_type == 'forecast']
RISK_SCORE_SERVICES = [name for name, item in SERVICE_CATALOG.items() if item.task_type == 'risk_score']

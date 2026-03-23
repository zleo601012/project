FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PORT=8000 \
    MODEL_DIR=/app/services/flow_forecast_service/artifacts

WORKDIR /app

RUN mkdir -p /app/services/flow_forecast_service \
    && touch /app/services/__init__.py

COPY . /app/services/flow_forecast_service

EXPOSE 8000

CMD ["python", "-m", "services.flow_forecast_service.server"]

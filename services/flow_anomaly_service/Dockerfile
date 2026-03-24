FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    MODEL_DIR=/app/flow_anomaly_service/artifacts

WORKDIR /app

COPY . /app/flow_anomaly_service

EXPOSE 8000

CMD ["python", "-m", "flow_anomaly_service.server"]

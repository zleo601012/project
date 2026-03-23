FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PORT=8000

WORKDIR /app

COPY . /app

EXPOSE 8000

CMD ["python", "-m", "services.cod_anomaly_service.server"]

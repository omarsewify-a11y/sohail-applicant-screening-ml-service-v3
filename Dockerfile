# Sohail Applicant Screening ML Service — v3
# Builds and runs the API layer, with access to Khaled's frozen model
# and Omar's shared monitoring log.

FROM python:3.11-slim

WORKDIR /app

# Copy only what the API needs to run: its own code, the frozen model,
# and the monitoring folder (for the shared predictions log).
COPY api/ /app/api/
COPY data_training/model_v3.joblib /app/data_training/model_v3.joblib
COPY monitoring/predictions_log.csv /app/monitoring/predictions_log.csv

RUN pip install --no-cache-dir -r /app/api/requirements.txt

WORKDIR /app/api

# Absolute paths inside the container (main.py falls back to relative
# paths for local dev; these env vars override that in Docker).
ENV MODEL_PATH=/app/data_training/model_v3.joblib
ENV LOG_PATH=/app/monitoring/predictions_log.csv

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

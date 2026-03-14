FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_HOME=/app

WORKDIR ${APP_HOME}

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl gcc git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt

COPY src ./src
COPY notebooks ./notebooks
COPY scripts ./scripts
COPY data ./data
COPY manifests ./manifests

RUN mkdir -p /app/runtime_logs

ENV PYTHONPATH=/app/src

CMD ["python", "-m", "kg_framework.cli", "run-all"]

FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt

COPY src ./src
COPY tests ./tests

ENV PYTHONPATH=/app/src

CMD ["uvicorn", "biomedical_api.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]

FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

WORKDIR /app
COPY . /app

RUN uv sync --frozen

EXPOSE 8000

WORKDIR /app/backend

CMD uv run --project /app uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}

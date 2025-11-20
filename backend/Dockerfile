
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libgl1 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend /app
ENV PYTHONPATH=/app

RUN mkdir -p /app/../data/saved && mkdir -p /app/../data/persons

CMD ["gunicorn", "-c", "gunicorn_conf.py", "main:app"]

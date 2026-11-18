FROM python:3.13-slim-bookworm

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
COPY processing/requirements-thumbnail.txt ./processing/requirements-thumbnail.txt
RUN pip install --no-cache-dir -r requirements.txt

RUN useradd --system --user-group --no-create-home app && install -d -m 0700 -o app -g app /var/lib/kho-tri-thuc/staging /var/lib/kho-tri-thuc/thumbnails
COPY . .
USER app

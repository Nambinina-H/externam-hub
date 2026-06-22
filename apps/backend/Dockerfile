FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dépendances système (psycopg2)
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Applique les migrations puis démarre l'API (FastAPI CLI, mode production).
# Le port vient de $PORT s'il est fourni (Railway/PaaS l'injectent), sinon 8000.
CMD ["sh", "-c", "alembic upgrade head && fastapi run app/main.py --host 0.0.0.0 --port ${PORT:-8000}"]

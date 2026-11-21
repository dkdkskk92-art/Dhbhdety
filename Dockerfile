FROM python:3.11-slim

WORKDIR /app

# Устанавливаем только минимально необходимые системные пакеты для asyncpg и сборки
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV PORT=3000

CMD ["python", "run.py"]

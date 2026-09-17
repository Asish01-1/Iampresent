FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgles2 \
    libegl1 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend

WORKDIR /app/backend

CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT}"]

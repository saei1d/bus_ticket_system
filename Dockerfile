# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# نصب وابستگی‌های سیستم (برای asyncpg)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# کپی requirements و نصب
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# کپی کد
COPY . .

# اجرای برنامه
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
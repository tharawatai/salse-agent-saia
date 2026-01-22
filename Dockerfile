FROM python:3.11-slim

WORKDIR /app

# تثبيت المتطلبات النظامية
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# نسخ المتطلبات
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ الكود
COPY . .

# إنشاء مجلدات
RUN mkdir -p logs media staticfiles

# جمع الملفات الثابتة
RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

CMD ["gunicorn", "saia_insurance.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]

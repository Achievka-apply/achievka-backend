### backend/Dockerfile

# 1. Базовый образ — компактный Python
FROM python:3.10-slim

# 2. Устанавливаем системные зависимости
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 3. Рабочая директория
WORKDIR /app

=======

# 4. Копируем зависимости и устанавливаем их
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

>>>>>>> main
# 5. Копируем весь код приложения
COPY . .

# 6. Генерируем статику
#RUN python manage.py collectstatic --no-input

# 7. Открываем порт для приложения
EXPOSE 8080
=======

# 8. Команда по умолчанию — запуск Gunicorn
CMD ["gunicorn", "achievka_backend.wsgi:application", "--bind", "0.0.0.0:8080", "--workers", "3"]

>>>>>>> main

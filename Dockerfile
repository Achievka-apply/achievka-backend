# Базовый образ Python
FROM python:3.11-slim

# Не сохранять .pyc и не буферизовать вывод
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Рабочая директория внутри контейнера
WORKDIR /app

# Установить системные зависимости (для Postgres)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копировать и установить Python-зависимости
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Скопировать весь код проекта
COPY . .

# Добавить и сделать исполняемым entrypoint
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Запуск скрипта entrypoint при старте контейнера
ENTRYPOINT ["./entrypoint.sh"]

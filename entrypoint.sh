#!/usr/bin/env bash
set -e

# 1) Применить миграции
python manage.py migrate --noinput

# 2) Собрать статику
python manage.py collectstatic --noinput

# 3) Запустить Gunicorn
exec gunicorn achievka_backend.wsgi:application \
     --bind 0.0.0.0:8000 \
     --workers 3 \
     --log-level info

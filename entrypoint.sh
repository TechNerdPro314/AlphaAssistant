#!/bin/sh

# Останавливаем выполнение при любой ошибке
set -e

echo "Waiting for database to be ready..."
# Даем время на инициализацию, если это необходимо
sleep 2

# Применяем миграции базы данных
echo "Running database migrations..."
flask db upgrade

echo "Database migrations complete."

# Запускаем основную команду, переданную в Dockerfile (gunicorn)
exec "$@"
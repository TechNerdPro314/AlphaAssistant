# Шаг 1: Используем официальный, легковесный образ Python
FROM python:3.10-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Устанавливаем переменные окружения, чтобы Python не буферизовал вывод
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Шаг 2: Установка зависимостей
# Копируем только файл с зависимостями, чтобы использовать кэширование Docker
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Шаг 3: Копирование кода приложения и стартового скрипта
# Копируем стартовый скрипт и делаем его исполняемым
COPY entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh

# Копируем весь остальной код приложения
COPY . .

# Шаг 4: Указываем порт, который будет слушать приложение
EXPOSE 5000

# Шаг 5: Указываем стартовый скрипт и команду по умолчанию
ENTRYPOINT ["entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app"]
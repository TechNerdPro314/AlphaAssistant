# Шаг 1: Используем официальный, легковесный образ Python
FROM python:3.12-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# --- Начало секции установки сертификатов ---
# Обновляем списки пакетов и устанавливаем необходимые утилиты
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Создаем специальную директорию для внешних сертификатов
RUN mkdir -p /usr/local/share/ca-certificates/extra

# Скачиваем российские корневые сертификаты в эту директорию
RUN curl -ksSL "https://gu-st.ru/content/Other/doc/russian_trusted_root_ca_pem.crt" -o /usr/local/share/ca-certificates/extra/russian-trusted-root-ca.crt && \
    curl -ksSL "https://gu-st.ru/content/Other/doc/russian_trusted_sub_ca_pem.crt" -o /usr/local/share/ca-certificates/extra/russian-trusted-sub-ca.crt

# Обновляем системное хранилище сертификатов. Эта команда найдет новые .crt файлы и добавит их.
RUN update-ca-certificates
# --- Конец секции ---

# Устанавливаем переменные окружения, чтобы Python не буферизовал вывод
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Шаг 2: Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Шаг 3: Копирование кода приложения и стартового скрипта
COPY entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh
COPY . .

# Шаг 4: Указываем порт
EXPOSE 5000

# Шаг 5: Указываем команду запуска с подробным логированием
ENTRYPOINT ["entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--log-level=debug", "--access-logfile=-", "--error-logfile=-", "run:app"]
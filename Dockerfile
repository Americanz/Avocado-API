# Використовуємо офіційний образ Python
FROM python:3.11-slim

# Встановлюємо необхідні інструменти
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Встановлюємо poetry
RUN pip install --no-cache-dir poetry

# Встановлюємо робочу директорію в контейнері
WORKDIR /app

# Копіюємо файли poetry
COPY pyproject.toml poetry.lock* ./

# Налаштовуємо poetry для НЕ створення віртуального середовища
RUN poetry config virtualenvs.create false

# Встановлюємо залежності
RUN poetry install --no-root

# Копіюємо решту файлів проекту
COPY . .

# Створюємо необхідні директорії та встановлюємо права
RUN mkdir -p /data_db /app/logs \
    && chmod -R 777 /data_db /app/logs

# Делаем entrypoint-скрипт исполняемым
RUN chmod +x /app/docker-entrypoint.sh

# Відкриваємо порти
EXPOSE 8000

# Используем наш entrypoint-скрипт
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Встановлюємо команду за замовчуванням
CMD ["poetry", "run", "python", "run.py"]

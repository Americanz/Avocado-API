# Database Setup Guide

Цей документ описує налаштування локального середовища розробки з PostgreSQL та Redis у Docker контейнерах.

## Швидкий старт

```bash
# 1. Запуск одним скриптом
setup_local_dev.bat

# або ручний запуск:

# 2. Запуск контейнерів
docker compose -f docker/docker-compose.db.yml up -d

# 3. Перевірка підключення
python test_connections.py
```

## Налаштування

### PostgreSQL
- **Host**: `localhost`
- **Port**: `5432`
- **Database**: `avocado_db`
- **User**: `avocado_user`
- **Password**: `avocado_pass`

### Redis
- **Host**: `localhost`
- **Port**: `7379` (не стандартний, щоб не конфліктувати з локальним Redis)
- **Database**: `0`

## Файли конфігурації

### `.env` (Основні налаштування додатку)
```bash
# PostgreSQL
DATABASE_URL=postgresql+psycopg2://avocado_user:avocado_pass@localhost:5432/avocado_db
ASYNC_DATABASE_URL=postgresql+asyncpg://avocado_user:avocado_pass@localhost:5432/avocado_db

# Redis
REDIS_HOST=localhost
REDIS_PORT=7379
REDIS_DB=0
```

### `docker/docker-compose.db.yml` (Docker контейнери)
- PostgreSQL 15 Alpine
- Redis 7 Alpine
- Персистентні volumes
- Health checks
- Налаштування мережі

## Корисні команди

```bash
# Управління контейнерами
docker/manage_db.bat up       # Запуск
docker/manage_db.bat down     # Зупинка
docker/manage_db.bat restart  # Перезапуск
docker/manage_db.bat status   # Статус
docker/manage_db.bat logs     # Логи

# Підключення до БД
docker/manage_db.bat psql     # PostgreSQL CLI
docker/manage_db.bat redis    # Redis CLI

# Тестування
docker/manage_db.bat test     # Тест підключень
```

## Файлова структура

```
docker/
├── docker-compose.db.yml     # Docker Compose конфігурація
├── redis.conf               # Налаштування Redis
├── init/
│   └── 01-init.sql          # Ініціалізація PostgreSQL
├── manage_db.bat            # Скрипт управління
└── README.md               # Детальний опис Docker setup

.env                         # Змінні середовища додатку
stack.env                    # Альтернативні налаштування
test_connections.py          # Скрипт тестування з'єднань
setup_local_dev.bat         # Автоматичне налаштування
```

## Troubleshooting

### Порт вже зайнятий
```bash
# Перевірити що використовує порт
netstat -ano | findstr :5432
netstat -ano | findstr :7379

# Зупинити існуючі контейнери
docker compose -f docker/docker-compose.db.yml down
```

### Очищення даних
```bash
# Видалити контейнери та дані
docker compose -f docker/docker-compose.db.yml down -v

# Видалити volumes
docker volume rm docker_pg_data docker_redis_data
```

### Перевірка health status
```bash
docker compose -f docker/docker-compose.db.yml ps
```

## Інтеграція з FastAPI

Після запуску контейнерів додаток автоматично підключиться до:
- PostgreSQL: через SQLAlchemy (синхронно/асинхронно)
- Redis: через redis-py

Міграції Alembic та інші компоненти працюватимуть з PostgreSQL як з основною БД.
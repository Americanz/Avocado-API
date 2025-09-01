# Avocado API

API для роботи з даними системи управління бізнесом Avocado.

## Технології

- FastAPI - сучасний, швидкий веб-фреймворк для Python
- SQLAlchemy - ORM для роботи з базами даних
- Alembic - інструмент для міграцій бази даних
- PostgreSQL - реляційна база даних
- Pydantic - бібліотека для валідації даних
- JWT - для аутентифікації та авторизації
- Docker - для контейнеризації додатку

## Початок роботи

### Локальне налаштування

1. Клонуйте репозиторій:
```bash
git clone <repository-url>
cd avocado
```

2. Створіть віртуальне середовище та встановіть залежності з Poetry:
```bash
poetry install
```

3. Активуйте віртуальне середовище:
```bash
poetry shell
```

4. Налаштуйте змінні середовища у файлі `.env` (або використовуйте вже наявний).



5. Запустіть міграції для створення структури бази даних:
```bash
alembic revision --autogenerate -m "add_tables"
alembic upgrade head




alembic stamp head
```

6. Запустіть сервер для розробки:
```bash
python run.py
```

Сервер буде доступний за адресою http://localhost:8000.

### Використання Docker

1. Запустіть додаток за допомогою Docker Compose:
```bash
docker-compose up -d
```

Сервер буде доступний за адресою http://localhost:8000.

## API документація

Після запуску сервера, документація API буде доступна за наступними URL:

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
- OpenAPI специфікація: http://localhost:8000/api/openapi.json

## Структура проекту

```
├── alembic/              # Конфігурація та міграції Alembic
├── src/                  # Основний код додатку
│   ├── config/           # Конфігурація додатку
│   ├── core/             # Основні модулі (база даних, винятки, безпека)
│   ├── modules/          # Функціональні модулі системи
│   └── main.py           # Головний файл додатку
├── tests/                # Тести
├── .env                  # Змінні середовища
├── alembic.ini           # Конфігурація Alembic
├── docker-compose.yml    # Конфігурація Docker Compose
├── Dockerfile            # Конфігурація Docker
├── pyproject.toml        # Конфігурація проекту та залежностей
└── run.py                # Скрипт для запуску додатку
```

## Розробка

### Створення нових міграцій

Після внесення змін у моделі даних, створіть нову міграцію:

```bash
alembic revision --autogenerate -m "Description of changes"
```

Застосуйте нову міграцію:

```bash
alembic upgrade head
```

alembic current

### Створення нових модулів

Кожен функціональний модуль повинен мати наступну структуру:

```
modules/
└── my_module/
    ├── __init__.py
    ├── controller.py     # Бізнес-логіка
    ├── model.py          # SQLAlchemy моделі
    ├── routes.py         # FastAPI маршрути
    └── schemas.py        # Pydantic схеми
```

## Розгортання

### Підготовка до виробництва

1. Змініть налаштування у файлі `.env` для виробничого середовища, особливо:
   - `DEBUG=False`
   - Надійний `JWT_SECRET_KEY`
   - Коректні налаштування бази даних

2. Зберіть та запустіть Docker контейнер:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

host.docker.internal



## Ліцензія

[MIT](LICENSE)

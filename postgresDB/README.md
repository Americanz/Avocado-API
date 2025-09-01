# PostgreSQL Database Management for LUCHAN

This directory contains Docker configuration, management scripts, and custom PostgreSQL functions for the LUCHAN project.

## 📁 Структура файлів

### 🐳 Docker та управління

- `docker-compose.db.yml` - Docker Compose configuration for PostgreSQL and Redis
- `start_services.bat` - Start database services
- `stop_services.bat` - Stop database services
- `status.bat` - Check services status
- `show_logs.bat` - Show database logs
- `manage_db.bat` - Database management menu
- `redis.conf` - Redis configuration

### 🔧 PostgreSQL функції

- `business_analytics_functions.sql` - Бізнес-аналітичні функції для звітності
- `operational_functions.sql` - Операційні функції для щоденної роботи
- `deploy_functions.py` - Скрипт для розгортання функцій в БД

## 🚀 Використання

### Запуск сервісів

```bash
start_services.bat
```

### Зупинка сервісів

```bash
stop_services.bat
```

### Перевірка статусу

```bash
status.bat
```

### Перегляд логів

```bash
show_logs.bat
```

### Розгортання PostgreSQL функцій

```bash
# Перейти в папку postgresDB
cd postgresDB

# Запустити розгортання
python deploy_functions.py
```

## 📊 PostgreSQL Функції

### 🏢 Бізнес-аналітичні функції (business_analytics_functions.sql)

1. **get_spot_revenue(spot_id, start_date, end_date)** - Аналіз доходів точки
2. **get_client_analytics(client_id, start_date, end_date)** - Аналітика клієнта
3. **get_top_products(start_date, end_date, limit)** - Топ продуктів за період
4. **get_seasonal_analytics(year)** - Сезонна аналітика продажів
5. **get_rfm_analysis(months_back)** - RFM аналіз клієнтів

### ⚡ Операційні функції (operational_functions.sql)

1. **find_client_transactions(phone, name, limit)** - Швидкий пошук транзакцій клієнта
2. **get_spot_hourly_performance(spot_id, date)** - Продуктивність точки по годинах
3. **detect_sales_anomalies(date, threshold)** - Виявлення аномалій в продажах
4. **get_new_client_conversion(start_date, end_date)** - Конверсія нових клієнтів
5. **forecast_sales(spot_id, days)** - Прогноз продажів

## 💡 Приклади використання

### Аналіз доходів точки за місяць

```sql
SELECT * FROM get_spot_revenue(1, '2025-08-01', '2025-08-31');
```

### Пошук транзакцій клієнта за телефоном

```sql
SELECT * FROM find_client_transactions('+380501234567');
```

### Виявлення аномалій в продажах за сьогодні

```sql
SELECT * FROM detect_sales_anomalies();
```

### Топ-10 продуктів за місяць

```sql
SELECT * FROM get_top_products('2025-08-01', '2025-08-31', 10);
```

### RFM аналіз клієнтів за останні 6 місяців

```sql
SELECT * FROM get_rfm_analysis(6);
```

## 🔐 Підключення до БД

**Хост:** localhost
**Порт:** 5432
**База:** luchan_db
**Користувач:** postgres
**Пароль:** дивитись в .env файлі

## 📝 Примітки

- Всі функції оптимізовані для великих обсягів даних
- Використовуються індекси для швидкодії
- Функції мають параметри за замовчуванням для зручності
- Результати включають розрахункові метрики та аналітику
  - Автоматично підключається до PostgreSQL
  - Дизайн: Lucas theme

## Змінні для підключення

**PostgreSQL (для додатку):**

- HOST: `localhost` (зовнішнє підключення)
- PORT: `5432`
- USER: `avocado_user`
- PASSWORD: `avocado_pass`
- DB: `avocado_db`

**Redis (для додатку):**

- HOST: `localhost` (зовнішнє підключення)
- PORT: `7379`
- DB: `0`

**Adminer (веб-інтерфейс):**

- URL: http://localhost:8080
- Сервер: postgres (або localhost:5432)
- Користувач: avocado_user
- Пароль: avocado_pass
- База даних: avocado_db

## Перевірка підключення

```bash
# PostgreSQL
psql -h localhost -p 5432 -U avocado_user -d avocado_db

# Redis
redis-cli -h localhost -p 7379 ping
```

## Логи

```bash
# Переглянути логи всіх сервісів
docker compose -f docker/docker-compose.db.yml logs

# Логи конкретного сервісу
docker compose -f docker/docker-compose.db.yml logs postgres
docker compose -f docker/docker-compose.db.yml logs redis
docker compose -f docker/docker-compose.db.yml logs adminer
```

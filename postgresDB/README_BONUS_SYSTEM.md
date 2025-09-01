# Бонусна система - PostgreSQL

## 📋 Опис
Повна система автоматичного розрахунку бонусів для клієнтів з підтримкою тригерів PostgreSQL.

## 🚀 Швидке розгортання

### 1. Застосування основних тригерів
```bash
# В основній папці проекту
docker exec -i avocado_postgres psql -U avocado_user -d avocado_db < postgresDB/bonus_triggers.sql
```

### 2. Перевірка встановлення
```sql
-- Перевірити налаштування
SELECT * FROM system_settings WHERE key LIKE 'bonus%';

-- Перевірити тригери
SELECT event_object_table, trigger_name, action_timing, event_manipulation 
FROM information_schema.triggers 
WHERE trigger_name = 'trigger_process_bonus_operations';
```

## 🔧 Ключові особливості

### Валютний формат
- **clients.bonus**: зберігається в копійках × 100 (для точності)
- **transaction_bonus.amount**: зберігається в копійках
- **Розрахунки**: виконуються в гривнях, потім конвертуються

### Українські описи
- Всі описи бонусних операцій українською мовою
- "Нарахування X% бонусів за транзакцію #ID"
- "Оплата бонусами за транзакцію #ID"

### Захист від дублікатів
- Автоматична перевірка існуючих операцій
- NULL-безпечна обробка всіх значень

## 📊 Корисні функції

### Управління тригерами
```sql
-- Увімкнути бонусну систему
SELECT manage_bonus_triggers(true);

-- Вимкнути бонусну систему  
SELECT manage_bonus_triggers(false);
```

### Пересчет бонусів
```sql
-- Повний пересчет всіх бонусів
SELECT * FROM recalculate_all_bonuses_with_trigger();
```

### Налаштування системи
```sql
-- Встановити дату початку
SELECT set_setting('bonus_system_start_date', '2025-09-01');

-- Увімкнути/вимкнути систему
SELECT set_setting('bonus_system_enabled', 'true');
```

## 🛠️ Скрипти для роботи

### Перевірка клієнта
```bash
cd script
python check_client_bonus.py <client_id>
```

### Синхронізація транзакцій
```bash
cd script/sync
python sync_poster_receipts.py today
```

## 📈 Моніторинг

### Перевірка статистики
```sql
SELECT 
    operation_type,
    COUNT(*) as operations_count,
    SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) / 100.0 as total_earned_grn,
    SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) / 100.0 as total_spent_grn
FROM transaction_bonus 
GROUP BY operation_type;
```

### Топ клієнтів за бонусами
```sql
SELECT 
    c.client_id,
    c.name,
    c.phone,
    c.bonus / 100.0 as bonus_balance_grn
FROM clients c 
WHERE c.bonus > 0 
ORDER BY c.bonus DESC 
LIMIT 10;
```

## ⚠️ Важливі нотатки

1. **Резервне копіювання**: Обов'язково створіть backup перед застосуванням
2. **Тестування**: Спочатку протестуйте на тестовій базі
3. **Моніторинг**: Відстежуйте логи після встановлення
4. **Валюта**: Всі розрахунки враховують формат копійки × 100

## 🔍 Діагностика

### Перевірка помилок
```sql
-- Останні повідомлення в логах
SELECT * FROM pg_stat_activity WHERE query LIKE '%bonus%';
```

### Перевірка цілісності
```bash
python script/check_client_bonus.py <client_id>
```

Файл буде показувати розбіжності між розрахунковим та фактичним балансом.

## 📞 Підтримка

Всі файли знаходяться в папці `postgresDB/`:
- `bonus_triggers.sql` - основний файл з тригерами
- `fix_bonus_function_v5_ukr.sql` - останні виправлення

Для розгортання нового проекту достатньо виконати `bonus_triggers.sql`.

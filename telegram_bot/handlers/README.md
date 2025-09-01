# Структура обробників Telegram-бота

Ця папка містить організовану структуру обробників для Telegram-бота, розділену на логічні модулі.

## Структура папок

```
handlers/
├── common/          # Загальні компоненти
│   ├── __init__.py
│   ├── permissions.py    # Управління правами доступу
│   ├── dispatcher.py     # Диспетчер кнопок
│   ├── balance.py       # Обробники балансу (legacy)
│   ├── history.py       # Обробники історії (legacy)
│   ├── admin.py         # Загальні адмін функції (legacy)
│   ├── bonus.py         # Обробники бонусів (legacy)
│   └── share_phone.py   # Обробка номера телефону
├── user/            # Обробники для користувачів
│   ├── __init__.py
│   ├── basic.py         # Основні команди (/start, echo)
│   └── bonus.py         # Функції бонусів для користувача
├── admin/           # Обробники для адміністраторів
│   ├── __init__.py
│   ├── panel.py         # Панель адміністратора
│   └── bonus.py         # Управління бонусами
├── main.py          # Головний файл реєстрації
├── registry.py      # Реєстрація всіх обробників
└── __init__.py      # Головний модуль (legacy)
```

## Основні компоненти

### common/permissions.py

- `ADMIN_USER_IDS` - список ID адміністраторів
- `is_admin(user_id)` - перевірка прав адміністратора
- `get_admin_ids()` - отримання списку адмінів

### common/dispatcher.py

- `register_button_handler(name)` - декоратор для реєстрації обробника кнопки
- `dispatch_button_handler(name, message, state)` - виклик обробника кнопки
- `button_handlers` - словник зареєстрованих обробників

### user/basic.py

- `register_user_handlers(dp, menu_manager)` - реєстрація базових обробників
- Обробка команди `/start`
- Основний echo handler для меню
- Обробка реєстрації номера телефону

### user/bonus.py

- `view_bonus_history()` - перегляд історії бонусів
- `view_balance()` - перегляд балансу користувача

### admin/panel.py

- `admin_panel()` - головна панель адміністратора
- `admin_stats()` - статистика системи
- `admin_users()` - управління користувачами
- `admin_back()`, `admin_back_to_panel()` - навігація

### admin/bonus.py

- `admin_bonuses()` - панель управління бонусами
- `add_bonus()` - додавання бонусів користувачу
- `remove_bonus()` - зняття бонусів з користувача

## Використання

### Реєстрація обробників

```python
from telegram_bot.handlers.main import register_all_handlers

# В bot.py
register_all_handlers(dp, menu_manager)
```

### Створення нового обробника користувача

```python
# user/my_handler.py
from telegram_bot.navigation.decorators import button_handler

@button_handler
async def my_user_function(message: Message):
    await message.answer("Відповідь користувачу")
```

### Створення нового обробника адміністратора

```python
# admin/my_admin_handler.py
from telegram_bot.handlers.common.permissions import is_admin
from telegram_bot.navigation.decorators import button_handler

@button_handler
async def my_admin_function(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ Доступ лише для адміністратора.")
        return

    await message.answer("Адмін функція")
```

## Міграція зі старої структури

Стара структура (`procedures/`) підтримується для сумісності, але нові обробники рекомендується створювати в новій структурі:

- **Користувацькі функції** → `user/`
- **Адміністративні функції** → `admin/`
- **Загальні компоненти** → `common/`

## Переваги нової структури

1. **Логічне розділення** - користувачі та адміни в окремих папках
2. **Переважування прав** - централізована перевірка в `common/permissions.py`
3. **Модульність** - легко додавати нові функції
4. **Сумісність** - стара структура продовжує працювати
5. **Тестування** - легше тестувати окремі модулі

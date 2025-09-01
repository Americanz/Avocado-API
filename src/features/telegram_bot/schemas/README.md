# Telegram Bot Service Functions

Цей пакет містить сервіс-функції для роботи телеграм бота з уніфікованими моделями. Замість дублікатних схем використовуються функції, які повертають словники з даними.

## Структура

```
schemas/
├── __init__.py          # Головний файл з усіма імпортами
├── user.py             # Функції для роботи з користувачами
├── receipt.py          # Функції для роботи з чеками
├── product.py          # Функції для роботи з продуктами
├── bonus.py            # Функції для роботи з бонусами
├── store.py            # Функції для роботи з магазинами
└── README.md           # Цей файл
```

## Використання

### Старий код:

```python
from src.features.telegram_bot.model import TelegramBotUser

user = session.query(TelegramBotUser).filter(...).first()
# Не працює більше!
```

### Новий код:

```python
from src.features.telegram_bot.schemas import (
    get_telegram_user,
    create_or_update_telegram_user
)

# В обробнику телеграм бота:
def my_handler(session: Session, telegram_user_id: int):
    # Отримати користувача - повертає dict
    user = get_telegram_user(session, telegram_user_id)
    if user:
        print(f"User: {user['first_name']} {user['last_name']}")
        print(f"Phone: {user['phone']}")
        print(f"Username: @{user['username']}")

    # Створити або оновити користувача - повертає dict
    user = create_or_update_telegram_user(
        session,
        telegram_user_id=telegram_user_id,
        username="john_doe",
        first_name="John",
        last_name="Doe",
        phone="+380123456789"
    )
```

### Робота з чеками:

```python
from src.features.telegram_bot.schemas import (
    get_user_receipts,
    get_receipt_details
)

# Отримати чеки користувача - повертає list[dict]
receipts = get_user_receipts(session, telegram_user_id, limit=10)
for receipt in receipts:
    print(f"Receipt {receipt['receipt_number']}: {receipt['total_amount']} UAH")

# Детальна інформація про чек - повертає dict
details = get_receipt_details(session, receipt_id="12345")
if details:
    print(f"Store: {details['spot_name']}")
    print(f"Items: {len(details['items'])}")
```

### Робота з бонусами:

```python
from src.features.telegram_bot.schemas import (
    get_user_bonus_balance,
    add_bonus_to_user,
    get_user_bonus_history
)

# Баланс бонусів
balance = get_user_bonus_balance(session, telegram_user_id)
print(f"Balance: {balance}")

# Додати бонуси
add_bonus_to_user(session, telegram_user_id, 100, "Welcome bonus")

# Історія бонусів
history = get_user_bonus_history(session, telegram_user_id)
for transaction in history:
    print(f"{transaction.amount} - {transaction.description}")
```

## Переваги нового підходу

1. **Зворотна сумісність** - старий код телеграм бота працює з мінімальними змінами
2. **Уніфіковані дані** - користувачі зберігаються в Client, а не дублюються
3. **Автоматична синхронізація** - дані з Poster API автоматично доступні в телеграм боті
4. **Чисті інтерфейси** - телеграм бот не знає про внутрішню структуру Poster моделей
5. **Гнучкість** - легко додавати нові поля або змінювати логіку

## Мапінг полей

### TelegramBotUser ← Client

- `user_id` ← `telegram_user_id`
- `username` ← `telegram_username`
- `first_name` ← `telegram_first_name` або `firstname`
- `last_name` ← `telegram_last_name` або `lastname`
- `phone` ← `phone`
- `is_active` ← `is_active`
- `is_blocked` ← `not is_telegram_active`
- `language_code` ← `telegram_language_code`

### TelegramReceipt ← Transaction

- `id` ← `id`
- `receipt_number` ← `transaction_id`
- `store_name` ← `spot_name`
- `total_amount` ← `sum`
- `discount` ← `discount`
- `date_created` ← `date_close`

### TelegramProduct ← Product

- `id` ← `id`
- `name` ← `product_name`
- `category` ← `category_name`
- `base_price` ← `cost`
- `barcode` ← `barcode`

## Міграція

Для міграції існуючого коду:

1. Замініть імпорти:

   ```python
   # Старий
   from src.features.telegram_bot.model import TelegramBotUser

   # Новий
   from src.features.telegram_bot.schemas import TelegramBotUser
   ```

2. Використовуйте функції замість прямих запитів:

   ```python
   # Старий
   user = session.query(TelegramBotUser).filter(TelegramBotUser.user_id == user_id).first()

   # Новий
   user = get_telegram_user(session, user_id)
   ```

3. Поля залишаються такими ж:
   ```python
   # Продовжує працювати
   print(user.first_name)
   print(user.phone)
   print(user.username)
   ```

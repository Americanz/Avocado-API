# Модуль автентифікації через Telegram

Цей модуль забезпечує автентифікацію користувачів через Telegram, надаючи більш зручний і безпечний метод авторизації порівняно з традиційними OTP.

## Огляд

Автентифікація через Telegram працює за подібним принципом як OTP, але замість введення коду вручну користувач просто натискає кнопку підтвердження в Telegram. Це робить процес більш зручним і менш схильним до помилок.

## Залежності та встановлення

### Необхідні пакети

Для роботи модуля потрібно встановити наступні пакети:

```bash
# Основні пакети
pip install python-telegram-bot==20.7 # Версія 20+ для підтримки async API
pip install httpx==0.25.2 # Для асинхронних HTTP запитів

# Додаткові залежності (якщо ще не встановлені)
pip install pydantic==2.5.2
pip install pyjwt==2.8.0
pip install pytz==2023.3
```

### Встановлення модуля

1. Скопіюйте всі файли модуля в директорію проекту:

   ```
   src/core/models/auth/telegram/
   ├── __init__.py
   ├── bot.py
   ├── controller.py
   ├── model.py
   ├── routes.py
   ├── schemas.py
   └── service.py
   ```

2. Додайте міграцію для створення таблиці `telegram_auth`:
   ```bash
   alembic revision --autogenerate -m "Add telegram_auth table"
   alembic upgrade head
   ```

## Як це працює

1. **Ініціація авторизації**:

   - Користувач вводить свій email на сайті
   - Система генерує унікальний код авторизації і зберігає його в базі даних
   - Користувач отримує посилання на Telegram бота

2. **Підтвердження в Telegram**:

   - Користувач переходить за посиланням до Telegram бота
   - Бот показує запит на підтвердження входу
   - Користувач натискає "Підтвердити"

3. **Завершення авторизації**:
   - Telegram бот повідомляє API про підтвердження
   - Користувач повертається на сайт і завершує процес входу
   - Система створює JWT токен і авторизує користувача

## Переваги перед OTP

- Не потрібно вводити коди вручну
- Використовує вбудовану систему безпеки Telegram
- Забезпечує швидкий вхід для користувачів, які вже авторизувались раніше
- Можливість використання даних з Telegram профілю
- Захист від фішингу через перевірку в обидві сторони

## Налаштування

### 1. Створіть Telegram бота

1. Відкрийте Telegram і знайдіть @BotFather
2. Надішліть команду `/newbot`
3. Дотримуйтесь інструкцій для створення нового бота
4. Збережіть токен бота, який вам надасть BotFather

### 2. Додайте налаштування в `settings.py`

```python
# Налаштування для Telegram автентифікації
ENABLE_TELEGRAM_AUTH = True
TELEGRAM_BOT_TOKEN = "your_bot_token_here"
TELEGRAM_BOT_USERNAME = "your_bot_username"
TELEGRAM_AUTH_EXPIRY_MINUTES = 15
API_BASE_URL = "https://your-api-domain.com"
WEBSITE_URL = "https://your-website-domain.com"
```

### 3. Додайте модуль до конфігурації

У файлі `src/core/loader/module_registry/config.py` додайте модуль до `BASE_MODULES`:

```python
BASE_MODULES = [
    # ...інші модулі...
    "src.core.models.auth.telegram",
]
```

### 4. Запустіть Telegram бота

Створіть окремий скрипт для запуску бота:

```python
# run_telegram_bot.py
import asyncio
from src.core.models.auth.telegram.bot import main

if __name__ == "__main__":
    main()
```

Запустіть бот:

```bash
python run_telegram_bot.py
```

Для продакшн-середовища рекомендується використовувати системи управління процесами:

**Supervisor конфігурація**:

```ini
[program:telegram_auth_bot]
command=python /path/to/your/app/run_telegram_bot.py
directory=/path/to/your/app
autostart=true
autorestart=true
stderr_logfile=/var/log/telegram_bot.err.log
stdout_logfile=/var/log/telegram_bot.out.log
environment=PYTHONPATH="/path/to/your/app"
```

**Docker конфігурація**:
Додайте окремий контейнер для бота у ваш `docker-compose.yml`:

```yaml
services:
  # ...інші сервіси...
  telegram_bot:
    build: .
    command: python run_telegram_bot.py
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - API_BASE_URL=${API_BASE_URL}
      - WEBSITE_URL=${WEBSITE_URL}
```

## API Ендпоінти

| Метод | URL                                    | Опис                                      |
| ----- | -------------------------------------- | ----------------------------------------- |
| POST  | `/telegram/request-link`               | Створює посилання для авторизації         |
| POST  | `/telegram/verify`                     | Перевіряє код авторизації і створює сесію |
| POST  | `/telegram/callback`                   | Приймає підтвердження від Telegram бота   |
| POST  | `/telegram/direct-login/{telegram_id}` | Прямий вхід за Telegram ID                |

## Схема бази даних

Модуль використовує таблицю `telegram_auth` з такими полями:

- `id`: Унікальний ідентифікатор запису (UUID)
- `auth_code`: Унікальний код авторизації
- `email`: Email користувача
- `telegram_id`: ID користувача в Telegram (після підтвердження)
- `telegram_username`: Username користувача в Telegram
- `is_used`: Чи був використаний код авторизації
- `expires_at`: Час закінчення терміну дії коду
- `processed_at`: Час обробки коду
- `created_at`: Час створення запису
- `updated_at`: Час останнього оновлення запису

## Вимоги до системи

- Python 3.8+
- PostgreSQL (або інша база даних, що підтримується SQLAlchemy)
- Доступ до Telegram API (не заблокований на рівні мережі)
- Маршрутизація зовнішніх запитів до API (для callback від Telegram бота)

## Інтеграція з фронтендом

### Приклад інтеграції з React

```jsx
import { useState } from "react";
import axios from "axios";

function TelegramLogin() {
  const [email, setEmail] = useState("");
  const [authLink, setAuthLink] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const requestAuthLink = async () => {
    setLoading(true);
    try {
      const response = await axios.post("/api/v1/telegram/request-link", {
        email,
      });
      if (response.data.status === "success") {
        setAuthLink(response.data.data.auth_link);
      } else {
        setError(response.data.msg || "Помилка запиту");
      }
    } catch (err) {
      setError("Сталася помилка при запиті");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="telegram-login">
      <h2>Увійти через Telegram</h2>

      {!authLink ? (
        <div className="request-form">
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Ваш email"
            required
          />
          <button onClick={requestAuthLink} disabled={loading}>
            {loading ? "Зачекайте..." : "Отримати посилання"}
          </button>
          {error && <div className="error">{error}</div>}
        </div>
      ) : (
        <div className="auth-link">
          <p>Перейдіть за посиланням для підтвердження:</p>
          <a
            href={authLink}
            target="_blank"
            rel="noopener noreferrer"
            className="telegram-button"
          >
            Підтвердити в Telegram
          </a>
          <p className="note">
            Після підтвердження поверніться на цю сторінку і натисніть кнопку
            "Перевірити"
          </p>
          <button onClick={() => window.location.reload()}>Перевірити</button>
        </div>
      )}
    </div>
  );
}

export default TelegramLogin;
```

## Безпека та обмеження

- Код авторизації має обмежений термін дії (за замовчуванням 15 хвилин)
- Кожен код можна використати лише один раз
- Передача даних між ботом і API захищена
- Інформація прив'язується до конкретного Telegram акаунту

## Усунення помилок

1. **Бот не відповідає**:

   - Перевірте, чи запущений процес бота
   - Перевірте правильність токена бота в налаштуваннях
   - Перевірте логи помилок бота

2. **Помилка "Could not connect to API"**:

   - Перевірте доступність API_BASE_URL з бота
   - Перевірте правильність URL у налаштуваннях
   - Переконайтеся, що мережеві порти відкриті і немає блокування фаєрволом

3. **Код авторизації не працює**:

   - Перевірте, чи не закінчився термін дії коду
   - Переконайтеся, що код не був використаний раніше
   - Перевірте логи на наявність помилок при валідації

4. **ImportError при запуску**:
   - Перевірте, чи всі залежності встановлені (`python-telegram-bot`, `httpx`)
   - Перевірте версії пакетів - потрібна python-telegram-bot версії 20+

## Додаткові можливості

- **Швидкий вхід**: Для користувачів, які вже підтвердили свій Telegram
- **Двофакторна автентифікація**: Використання Telegram як другого фактору
- **Прив'язка до бізнес-логіки**: Відправка сповіщень через Telegram після автентифікації
- **Webhook замість polling**: Для високонавантажених систем можна налаштувати webhook замість polling

## Ресурси та посилання

- [Документація Python Telegram Bot](https://python-telegram-bot.readthedocs.io/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [FastAPI документація](https://fastapi.tiangolo.com/)
- [SQLAlchemy документація](https://docs.sqlalchemy.org/)

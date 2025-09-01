# Navigation System для Telegram Bot

Цей модуль надає компонент для керування навігацією в Telegram боті, що базується на aiogram 3.
Система спроектована для підтримки багаторівневих меню, історії навігації та більш чистої організації коду.

## Переваги

- **Чистий код**: Відділення навігаційної логіки від хендлерів
- **Історія навігації**: Автоматичне відстеження попередніх меню для кнопок "Назад"
- **Централізоване керування меню**: Єдине місце для визначення структури меню
- **Декларативні хендлери**: Прості декоратори для реєстрації хендлерів кнопок
- **Підтримка мультимовності**: Працює з JSON-конфігурацією для текстів та кнопок
- **"Тихі" переходи**: Підтримка мінімальних повідомлень при навігації

## Структура

Система складається з наступних компонентів:

- `MenuManager`: Основний клас для керування меню та навігацією
- `NavigationState`: Керування станом навігації для кожного користувача
- `@button_handler`: Декоратор для реєстрації хендлерів кнопок

## Використання

### 1. Додавання системи до бота

```python
from telegram_bot.navigation import MenuManager
from telegram_bot.navigation.decorators import get_button_handlers

# Ініціалізуємо менеджер навігації
menu_manager = MenuManager()

# Реєструємо всі хендлери кнопок
for handler_name, handler_func in get_button_handlers().items():
    menu_manager.register_button_handler(handler_name, handler_func)

# Додаємо до диспетчера
dp = Dispatcher()
dp["menu_manager"] = menu_manager
```

### 2. Створення хендлерів кнопок

```python
from telegram_bot.navigation.decorators import button_handler

@button_handler("main_menu")
async def main_menu_handler(message: Message, **kwargs):
    """Handler для головного меню"""
    navigation = kwargs.get("navigation")
    await navigation.navigate_to(
        message=message,
        menu_name="main",
        text="Ласкаво просимо до головного меню"
    )

@button_handler("nav_back")
async def back_handler(message: Message, **kwargs):
    """Handler для кнопки назад"""
    navigation = kwargs.get("navigation")
    silent = kwargs.get("silent", False)
    await navigation.go_back(message, silent=silent)
```

### 3. Конфігурація меню в JSON

```json
{
  "main": [
    {
      "text": "Профіль",
      "enabled": true,
      "handler": "show_profile"
    },
    {
      "text": "Налаштування",
      "enabled": true,
      "handler": "show_settings"
    }
  ],
  "settings": [
    {
      "text": "Мова",
      "enabled": true,
      "handler": "change_language"
    },
    {
      "text": "⬅️ Назад",
      "enabled": true,
      "handler": "nav_back",
      "silent": true
    }
  ]
}
```

## Міграція з попередньої системи

Для міграції з попередньої системи необхідно:

1. Створити новий файл для хендлерів з використанням декоратора `@button_handler`
2. Оновити свої хендлери для використання параметра `navigation` з `kwargs`
3. Додати параметр `silent` до конфігурації кнопок "Назад"

## Підтримка зворотної сумісності

Система підтримує зворотну сумісність зі старим підходом через fallback:

```python
# Спочатку пробуємо через навігацію
if navigation:
    handled = await navigation.handle_button(message)
    if handled:
        return

# Якщо не оброблено - використовуємо старий підхід
handler = button_handlers.get(message.text)
if handler:
    await handler(message)
```

## Плани на майбутнє

- Підтримка inline-кнопок
- Глобальна фільтрація кнопок за правами
- Кеш меню для оптимізації продуктивності
- Додаткові типи меню (сторінки, карусель, тощо)

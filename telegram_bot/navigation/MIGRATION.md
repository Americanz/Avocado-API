# Migrations Guide: Moving to the Navigation System

This guide explains how to migrate your existing Telegram bot handlers to use the new navigation system.

## Step 1: Register your button handlers using the decorator

**Before:**

```python
@register_button_handler("admin_panel")
async def admin_panel(message: Message):
    # Handler implementation
    pass
```

**After:**

```python
from telegram_bot.navigation.decorators import button_handler

@button_handler("admin_panel")
async def admin_panel(message: Message, **kwargs):
    navigation = kwargs.get("navigation")
    # Handler implementation using navigation
    pass
```

## Step 2: Update your handlers to use navigation

**Before:**

```python
async def admin_panel(message: Message):
    # Direct keyboard creation
    admin_menu_buttons = [
        [
            types.KeyboardButton(text="Статистика"),
            types.KeyboardButton(text="Керування бонусами"),
            types.KeyboardButton(text="Керування користувачами"),
        ],
        [types.KeyboardButton(text="⬅️ Назад")],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=admin_menu_buttons, resize_keyboard=True
    )

    await message.answer(
        "Ви в адмін-панелі. Оберіть розділ для керування:",
        parse_mode="HTML",
        reply_markup=keyboard,
    )
```

**After:**

```python
async def admin_panel(message: Message, **kwargs):
    navigation = kwargs.get("navigation")

    # Navigate to admin menu
    await navigation.navigate_to(
        message=message,
        menu_name="admin",
        text="Ви в адмін-панелі. Оберіть розділ для керування:",
        parent_menu="main"
    )
```

## Step 3: Update back button handlers

**Before:**

```python
@register_button_handler("admin_back")
async def admin_back(message: Message):
    # Complicated back logic with keyboard creation
    keyboard_buttons = get_keyboard("main")
    if str(user_id) in ADMIN_USER_IDS:
        admin_buttons = [
            btn for btn in get_keyboard("admin") if btn["handler"] == "admin_panel"
        ]
        keyboard_buttons += admin_buttons

    # More logic for creating keyboard
    # Check for silent parameter
    await message.answer("◀️", reply_markup=keyboard)
```

**After:**

```python
@button_handler("nav_back")
async def nav_back(message: Message, **kwargs):
    navigation = kwargs.get("navigation")
    silent = kwargs.get("silent", False)

    # Simple navigation back
    await navigation.go_back(message, silent=silent)
```

## Step 4: Update your JSON menu configuration

**Before:**

```json
{
  "admin": [
    {
      "text": "⬅️ Назад",
      "enabled": true,
      "handler": "admin_back",
      "silent": true
    }
  ]
}
```

**After:**

```json
{
  "admin": [
    {
      "text": "⬅️ Назад",
      "enabled": true,
      "handler": "nav_back",
      "silent": true
    }
  ]
}
```

## Step 5: Gradual Migration

You can migrate your handlers one by one:

1. Start with the main navigation paths (main menu, admin panel)
2. Then migrate the leaf handlers (statistics, user management)
3. Finally, standardize all back buttons to use `nav_back`

During migration, the system will use the new navigation system when available and fall back to the legacy approach when needed.

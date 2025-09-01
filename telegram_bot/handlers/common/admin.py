import logging
from aiogram import types
from aiogram.types import Message
from telegram_bot.handlers.common.dispatcher import register_button_handler
from telegram_bot.services.bonus_service_universal import get_bonus_service
from telegram_bot.data.bot_texts import get_text
from telegram_bot.data.keyboards import get_keyboard
from telegram_bot.utils.datetime_helpers import format_date


@register_button_handler("admin_panel")
async def admin_panel(message: Message):
    logger = logging.getLogger("telegram_bot.handlers.admin")
    user_id = message.from_user.id
    logger.info(f"admin_panel для user_id={user_id}")
    try:
        bonus_service = get_bonus_service()
        if not bonus_service.table_exists("telegram_bonus_accounts"):
            text = (
                get_text("admin_table_missing")
                or "Таблиця bot_bonuses не існує. Створіть її у Supabase!"
            )
            await message.answer(text, parse_mode="HTML")
            return
        # Формуємо повідомлення
        text = (
            get_text("admin_panel")
            or "Ви в адмін-панелі. Оберіть розділ для керування:"
        )
        # Формуємо 3 адмін-кнопки в один ряд + кнопку назад під ними
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
            text,
            parse_mode="HTML",
            reply_markup=keyboard,
        )
        return
    except Exception as e:
        logger.error(f"Помилка в admin_panel: {e}")
        await message.answer(str(e))


@register_button_handler("admin_stats")
async def admin_stats(message: Message):
    logger = logging.getLogger("telegram_bot.handlers.admin")
    try:
        # Отримуємо статистику через адмін-сервіс
        bonus_service = get_bonus_service()
        recent_users = await bonus_service.admin_users(10)
        
        users_count = len(recent_users) if recent_users else 0
        phone_count = sum(1 for user in recent_users if user.get('phone')) if recent_users else 0

        stats_text = f"""📊 <b>Статистика бота:</b>

👥 <b>Користувачі (останні 10):</b>
• Всього в вибірці: {users_count}
• З номерами телефону: {phone_count}
• Без номерів: {users_count - phone_count}

📈 <b>Коефіцієнт конверсії:</b>
• {(phone_count/users_count*100) if users_count > 0 else 0:.1f}% користувачів поділилися номером
"""
    except Exception as e:
        logger.error(f"Помилка отримання статистики: {e}")
        stats_text = "❌ Помилка отримання статистики"

    await message.answer(
        stats_text,
        parse_mode="HTML",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="⬅️ Назад до адмін-панелі")]],
            resize_keyboard=True,
        ),
    )


@register_button_handler("admin_bonuses")
async def admin_bonuses(message: Message):
    logger = logging.getLogger("telegram_bot.handlers.admin")

    try:  # Отримуємо дані про бонуси через адмін-сервіс
        bonus_service = get_bonus_service()
        recent_users = await bonus_service.admin_users(5)

        bonuses_text = "💰 <b>Керування бонусами:</b>\n\n"

        if recent_users:
            bonuses_text += "📋 <b>Останні 5 користувачів з балансами:</b>\n"
            total_balance = 0
            active_users = 0
            
            for user in recent_users:
                user_id = user.get("client_id", "N/A")
                balance = user.get("bonus", 0)
                name = user.get("name", "Не вказано")
                if balance and balance > 0:
                    active_users += 1
                    total_balance += balance
                    balance_grn = float(balance) / 100.0  # конвертуємо з копійок
                    bonuses_text += f"• {name} (ID: {user_id}): {balance_grn:.2f} грн\n"
        else:
            bonuses_text += "📋 Користувачів з бонусами поки немає\n"
            total_balance = 0
            active_users = 0

        bonuses_text += f"\n💎 <b>Загальна сума балансів:</b> {float(total_balance) / 100.0:.2f} грн\n"
        bonuses_text += f"👥 <b>Користувачів з балансом > 0:</b> {active_users}\n"
        bonuses_text += "\n🔧 <b>Доступні дії:</b>\n• Нарахувати бонуси\n• Списати бонуси\n• Переглянути історію"

    except Exception as e:
        logger.error(f"Помилка отримання даних про бонуси: {e}")
        bonuses_text = "❌ Помилка отримання даних про бонуси"

    # Створюємо кнопки для керування бонусами
    bonus_keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [
                types.KeyboardButton(text="Нарахувати бонуси"),
                types.KeyboardButton(text="Списати бонуси"),
            ],
            [types.KeyboardButton(text="Переглянути історію")],
            [types.KeyboardButton(text="⬅️ Назад до адмін-панелі")],
        ],
        resize_keyboard=True,
    )

    await message.answer(
        bonuses_text,
        parse_mode="HTML",
        reply_markup=bonus_keyboard,
    )


@register_button_handler("admin_users")
async def admin_users(message: Message):
    logger = logging.getLogger("telegram_bot.handlers.admin")
    try:
        # Отримуємо дані про користувачів через админ-сервіс керування користувачами
        bonus_service = get_bonus_service()
        recent_users = await bonus_service.admin_users(10)

        users_text = "👥 <b>Керування користувачами:</b>\n\n"

        if recent_users:
            users_text += "📋 <b>Останні 10 користувачів:</b>\n"
            for user in recent_users:
                user_id = user.get("user_id", "N/A")
                username = user.get("username", "Без імені")
                phone = user.get("phone", "Не вказано")
                created_at = format_date(user.get("created_at", ""))

                phone_status = "📱" if phone != "Не вказано" else "❌"
                users_text += (
                    f"• {phone_status} {user_id} (@{username}) - {created_at}\n"
                )
        else:
            users_text += "📋 Користувачів поки немає\n"

        users_text += "\n🔧 <b>Доступні дії:</b>\n• Переглянути детальну інформацію\n• Заблокувати/розблокувати\n• Експорт списку користувачів"

    except Exception as e:
        logger.error(f"Помилка отримання даних про користувачів: {e}")
        users_text = "❌ Помилка отримання даних про користувачів"

    await message.answer(
        users_text,
        parse_mode="HTML",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="⬅️ Назад до адмін-панелі")]],
            resize_keyboard=True,
        ),
    )


@register_button_handler("admin_back")
async def admin_back(message: Message):
    """Повернення на головне меню з адмін-панелі"""
    logger = logging.getLogger("telegram_bot.handlers.admin")
    user_id = message.from_user.id
    logger.info(f"admin_back для user_id={user_id}")

    from telegram_bot.data.keyboards import get_keyboard
    from aiogram import types
    from telegram_bot.data.bot_texts import get_text
    from telegram_bot.handlers.common.permissions import is_admin
    from telegram_bot.states.phone_state import PhoneState

    # Головне меню: тільки main + (опціонально) "Адмін-панель"
    keyboard_buttons = get_keyboard("main")
    if is_admin(user_id):
        admin_buttons = [
            btn for btn in get_keyboard("admin") if btn["handler"] == "admin_panel"
        ]
        keyboard_buttons += admin_buttons

    # Перевіряємо кешований статус телефону
    has_phone = PhoneState.get(user_id)
    if not has_phone:
        # Якщо в кеші немає — перевіряємо у БД
        bonus_service = get_bonus_service()
        user = await bonus_service.get_user_by_id(user_id)
        if user and user.get("phone"):
            PhoneState.set(user_id, True)
            has_phone = True
        else:
            PhoneState.set(user_id, False)

    # Якщо телефон вже є — не показуємо кнопку "Поділитись номером"
    if has_phone:
        keyboard_buttons = [
            btn for btn in keyboard_buttons if btn["text"] != "Поділитись номером"
        ]

    buttons = [
        [
            types.KeyboardButton(text=btn["text"])
            for btn in keyboard_buttons
            if btn["enabled"]
        ]
    ]

    keyboard = types.ReplyKeyboardMarkup(
        keyboard=buttons, resize_keyboard=True
    )  # Перевіряємо чи кнопка має параметр silent
    admin_buttons_config = get_keyboard("admin")
    button_config = next(
        (btn for btn in admin_buttons_config if btn["handler"] == "admin_back"), None
    )

    if button_config and button_config.get("silent", False):
        # Тихий режим - мінімальне повідомлення з emoji замість тексту
        await message.answer("◀️", reply_markup=keyboard)
    else:
        # Звичайний режим - з повідомленням
        await message.answer(
            get_text("can_use_bot") or "Тепер ви можете користуватись ботом:",
            reply_markup=keyboard,
        )


@register_button_handler("admin_back_to_panel")
async def admin_back_to_panel(message: Message):
    """Повернення з підменю до адмін-панелі"""
    logger = logging.getLogger("telegram_bot.handlers.admin")
    user_id = message.from_user.id
    logger.info(f"admin_back_to_panel для user_id={user_id}")

    # Формуємо адмін-кнопки
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
    )  # Перевіряємо чи кнопка має параметр silent
    admin_buttons_config = get_keyboard("admin")
    button_config = next(
        (
            btn
            for btn in admin_buttons_config
            if btn["handler"] == "admin_back_to_panel"
        ),
        None,
    )

    if button_config and button_config.get("silent", False):
        # Тихий режим - мінімальне повідомлення з emoji замість тексту
        await message.answer("◀️", reply_markup=keyboard)
    else:
        # Звичайний режим - з повідомленням
        text = (
            get_text("admin_panel")
            or "Ви в адмін-панелі. Оберіть розділ для керування:"
        )
        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=keyboard,
        )

import logging
from decimal import Decimal
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
        if not bonus_service.table_exists("clients"):
            text = (
                get_text("admin_table_missing")
                or "Таблиця clients не існує в PostgreSQL!"
            )
            await message.answer(text, parse_mode="HTML")
            return
        # Формуємо повідомлення
        text = (
            get_text("admin_panel")
            or "Ви в адмін-панелі. Оберіть розділ для керування:"
        )

        # Використовуємо keyboard builder для красивого розміщення
        from telegram_bot.keyboards.builder import build_admin_keyboard

        admin_buttons = get_keyboard("admin")
        keyboard = build_admin_keyboard(admin_buttons)

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
        recent_users = await bonus_service.admin_users(15)

        users_count = len(recent_users) if recent_users else 0
        phone_count = (
            sum(1 for user in recent_users if user.get("phone")) if recent_users else 0
        )

        # Розрахунок загального балансу
        from decimal import Decimal
        total_balance = sum(Decimal(str(user.get("bonus", 0))) for user in recent_users) if recent_users else Decimal('0')
        total_balance_grn = float(total_balance) / 100.0  # Конвертуємо з копійок в гривні

        stats_text = f"""📊 <b>Статистика бота:</b>

👥 <b>Користувачі (останні {users_count}):</b>
• Всього активних: {users_count}
• З номерами телефону: {phone_count}
• Без номерів: {users_count - phone_count}

💰 <b>Бонусна система:</b>
• Загальний баланс: {total_balance_grn:.2f} грн
• Середній баланс: {(total_balance_grn/users_count) if users_count > 0 else 0:.2f} грн

📈 <b>Коефіцієнт конверсії:</b>
• {(phone_count/users_count*100) if users_count > 0 else 0:.1f}% користувачів поділилися номером

📋 <b>Деталі останніх користувачів:</b>
"""

        # Додаємо деталі користувачів
        for i, user in enumerate(recent_users[:5], 1):
            name = user.get("name", "Не вказано")
            phone = user.get("phone", "❌")
            balance = (float(Decimal(str(user.get("bonus", 0)))) / 100.0) if user.get("bonus") else 0.0
            telegram_id = user.get("telegram_user_id", "N/A")
            
            stats_text += f"\n{i}. <b>{name}</b>"
            if len(name) > 25:
                stats_text += f"\n   📞 {phone} | 💰 {balance:.2f} грн"
                stats_text += f"\n   🆔 TG: {telegram_id}"
            else:
                stats_text += f"\n   📞 {phone} | 💰 {balance:.2f} грн | 🆔 {telegram_id}"

    except Exception as e:
        logger.error(f"Помилка отримання статистики: {e}")
        stats_text = f"❌ Помилка отримання статистики: {e}"

    # Створюємо inline keyboard для навігації
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Оновити", callback_data="admin_stats_refresh"),
            InlineKeyboardButton(text="📋 Деталі", callback_data="admin_stats_details")
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад до панелі", callback_data="admin_back_to_panel_inline")
        ]
    ])

    await message.answer(
        stats_text,
        parse_mode="HTML",
        reply_markup=inline_keyboard,
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

    keyboard = types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

    # Перевіряємо чи кнопка має параметр silent
    admin_buttons_config = get_keyboard("admin")
    button_config = next(
        (btn for btn in admin_buttons_config if btn["handler"] == "admin_back"), None
    )

    if button_config and button_config.get("silent", False):
        # Тихий режим - мінімальний текст для зміни клавіатури
        try:
            await message.delete()  # Видаляємо повідомлення користувача
        except:
            pass
        await message.answer("Назад", reply_markup=keyboard)  # Простий текст
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
    )

    # Перевіряємо чи кнопка має параметр silent
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
        # Тихий режим - мінімальне повідомлення + нова клавіатура
        try:
            await message.delete()  # Видаляємо повідомлення користувача
        except:
            pass
        # Відправляємо простий текст з новою клавіатурою
        await message.answer("Назад", reply_markup=keyboard)  # Простий текст
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


# Callback handlers для inline keyboard
from aiogram.types import CallbackQuery
from telegram_bot.handlers.common.dispatcher import register_callback_handler

@register_callback_handler("admin_stats_refresh")
async def admin_stats_refresh_callback(callback: CallbackQuery):
    """Оновлення статистики через inline кнопку"""
    logger = logging.getLogger("telegram_bot.handlers.admin")
    logger.info(f"admin_stats_refresh від {callback.from_user.id}")
    
    try:
        # Отримуємо статистику напряму
        bonus_service = get_bonus_service()
        recent_users = await bonus_service.admin_users(15)

        users_count = len(recent_users) if recent_users else 0
        phone_count = (
            sum(1 for user in recent_users if user.get("phone")) if recent_users else 0
        )

        # Розрахунок загального балансу
        from decimal import Decimal
        total_balance = sum(Decimal(str(user.get("bonus", 0))) for user in recent_users) if recent_users else Decimal('0')
        total_balance_grn = float(total_balance) / 100.0  # Конвертуємо з копійок в гривні

        stats_text = f"""📊 <b>Статистика бота:</b>

👥 <b>Користувачі (останні {users_count}):</b>
• Всього активних: {users_count}
• З номерами телефону: {phone_count}
• Без номерів: {users_count - phone_count}

💰 <b>Бонусна система:</b>
• Загальний баланс: {total_balance_grn:.2f} грн
• Середній баланс: {(total_balance_grn/users_count) if users_count > 0 else 0:.2f} грн

📈 <b>Коефіцієнт конверсії:</b>
• {(phone_count/users_count*100) if users_count > 0 else 0:.1f}% користувачів поділилися номером

📋 <b>Деталі останніх користувачів:</b>
"""

        # Додаємо деталі користувачів
        for i, user in enumerate(recent_users[:5], 1):
            name = user.get("name", "Не вказано")
            phone = user.get("phone", "❌")
            balance = (float(Decimal(str(user.get("bonus", 0)))) / 100.0) if user.get("bonus") else 0.0
            telegram_id = user.get("telegram_user_id", "N/A")
            
            stats_text += f"\n{i}. <b>{name}</b>"
            if len(name) > 25:
                stats_text += f"\n   📞 {phone} | 💰 {balance:.2f} грн"
                stats_text += f"\n   🆔 TG: {telegram_id}"
            else:
                stats_text += f"\n   📞 {phone} | 💰 {balance:.2f} грн | 🆔 {telegram_id}"

        # Створюємо inline keyboard для навігації
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Оновити", callback_data="admin_stats_refresh"),
                InlineKeyboardButton(text="📋 Деталі", callback_data="admin_stats_details")
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад до панелі", callback_data="admin_back_to_panel_inline")
            ]
        ])

        await callback.message.edit_text(
            stats_text,
            parse_mode="HTML",
            reply_markup=inline_keyboard
        )
        await callback.answer("📊 Статистика оновлена")
    except Exception as e:
        logger.error(f"Помилка оновлення статистики: {e}")
        await callback.answer("❌ Помилка оновлення", show_alert=True)


@register_callback_handler("admin_stats_details")
async def admin_stats_details_callback(callback: CallbackQuery):
    """Показ детальної статистики"""
    logger = logging.getLogger("telegram_bot.handlers.admin")
    logger.info(f"admin_stats_details від {callback.from_user.id}")
    
    try:
        from decimal import Decimal
        bonus_service = get_bonus_service()
        all_users = await bonus_service.admin_users(50)  # Отримуємо більше користувачів
        
        if not all_users:
            await callback.answer("❌ Немає даних", show_alert=True)
            return
            
        details_text = f"📋 <b>Детальна статистика (останні {len(all_users)}):</b>\n\n"
        
        # Групуємо за статусом телефону
        with_phone = [u for u in all_users if u.get("phone")]
        without_phone = [u for u in all_users if not u.get("phone")]
        
        details_text += f"✅ <b>З телефонами ({len(with_phone)}):</b>\n"
        for user in with_phone[:10]:  # Показуємо перших 10
            name = user.get("name", "Не вказано")
            phone = user.get("phone", "❌")
            balance = (float(Decimal(str(user.get("bonus", 0)))) / 100.0) if user.get("bonus") else 0.0
            details_text += f"• {name[:20]} | {phone} | {balance:.2f} грн\n"
            
        if len(with_phone) > 10:
            details_text += f"... та ще {len(with_phone) - 10} користувачів\n"
            
        details_text += f"\n❌ <b>Без телефонів ({len(without_phone)}):</b>\n"
        for user in without_phone[:5]:  # Показуємо перших 5
            name = user.get("name", "Не вказано")
            balance = (float(Decimal(str(user.get("bonus", 0)))) / 100.0) if user.get("bonus") else 0.0
            tg_id = user.get("telegram_user_id", "N/A")
            details_text += f"• {name[:20]} | 🆔 {tg_id} | {balance:.2f} грн\n"
            
        if len(without_phone) > 5:
            details_text += f"... та ще {len(without_phone) - 5} користувачів\n"
        
        # Створюємо inline keyboard для повернення
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад до статистики", callback_data="admin_stats_refresh")]
        ])
        
        await callback.message.edit_text(
            details_text,
            parse_mode="HTML",
            reply_markup=back_keyboard
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Помилка показу деталей: {e}")
        await callback.answer("❌ Помилка завантаження деталей", show_alert=True)


@register_callback_handler("admin_back_to_panel_inline")
async def admin_back_to_panel_inline_callback(callback: CallbackQuery):
    """Повернення до адмін-панелі через inline кнопку"""
    logger = logging.getLogger("telegram_bot.handlers.admin")
    logger.info(f"admin_back_to_panel_inline від {callback.from_user.id}")
    
    try:
        # Формуємо inline keyboard для адмін-панелі
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        admin_inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
                InlineKeyboardButton(text="💰 Бонуси", callback_data="admin_bonuses")
            ],
            [
                InlineKeyboardButton(text="👥 Користувачі", callback_data="admin_users"),
                InlineKeyboardButton(text="⚙️ Налаштування", callback_data="admin_settings")
            ],
            [
                InlineKeyboardButton(text="🏠 Головне меню", callback_data="admin_back")
            ]
        ])
        
        admin_text = (
            get_text("admin_panel")
            or "Ви в адмін-панелі. Оберіть розділ для керування:"
        )
        
        await callback.message.edit_text(
            admin_text,
            parse_mode="HTML",
            reply_markup=admin_inline_keyboard
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Помилка повернення до панелі: {e}")
        await callback.answer("❌ Помилка навігації", show_alert=True)


# Додаткові callback handlers для inline кнопок адмін-панелі
@register_callback_handler("admin_stats")
async def admin_stats_inline_callback(callback: CallbackQuery):
    """Статистика через inline кнопку"""
    logger = logging.getLogger("telegram_bot.handlers.admin")
    logger.info(f"admin_stats (inline) від {callback.from_user.id}")
    
    try:
        # Викликаємо refresh функцію, яка вже має всю логіку
        await admin_stats_refresh_callback(callback)
    except Exception as e:
        logger.error(f"Помилка показу статистики: {e}")
        await callback.answer("❌ Помилка завантаження статистики", show_alert=True)


@register_callback_handler("admin_bonuses")
async def admin_bonuses_inline_callback(callback: CallbackQuery):
    """Бонуси через inline кнопку"""
    logger = logging.getLogger("telegram_bot.handlers.admin")
    logger.info(f"admin_bonuses (inline) від {callback.from_user.id}")
    
    try:
        # Отримуємо дані про бонуси через адмін-сервіс
        bonus_service = get_bonus_service()
        recent_users = await bonus_service.admin_users(5)

        bonuses_text = "💰 <b>Керування бонусами:</b>\n\n"

        if recent_users:
            bonuses_text += "📋 <b>Останні 5 користувачів з балансами:</b>\n"
            total_balance = 0
            active_users = 0

            for user in recent_users:
                user_id = user.get("client_id", "N/A")
                name = user.get("name", "Не вказано")
                bonus = user.get("bonus", 0)
                balance_grn = float(Decimal(str(bonus))) / 100.0
                total_balance += float(Decimal(str(bonus)))
                if bonus > 0:
                    active_users += 1

                bonuses_text += f"• {name[:20]} (#{user_id}): {balance_grn:.2f} грн\n"

            bonuses_text += f"\n📊 <b>Загальна статистика:</b>\n"
            bonuses_text += f"• Загальний баланс: {(total_balance/100):.2f} грн\n"
            bonuses_text += f"• Активних користувачів: {active_users}\n"
            bonuses_text += f"• Середній баланс: {(total_balance/100/len(recent_users)) if recent_users else 0:.2f} грн\n"
        else:
            bonuses_text += "📋 Користувачів з бонусами поки немає\n"

        bonuses_text += "\n🔧 <b>Доступні дії:</b>\n• Нарахувати/списати бонуси\n• Переглянути історію транзакцій\n• Експорт звіту по бонусах"

        # Створюємо inline keyboard
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="💳 Транзакції", callback_data="admin_transactions"),
                InlineKeyboardButton(text="📊 Звіт", callback_data="admin_bonus_report")
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад до панелі", callback_data="admin_back_to_panel_inline")
            ]
        ])

        await callback.message.edit_text(
            bonuses_text,
            parse_mode="HTML",
            reply_markup=inline_keyboard
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Помилка показу бонусів: {e}")
        await callback.answer("❌ Помилка завантаження", show_alert=True)


@register_callback_handler("admin_users")
async def admin_users_inline_callback(callback: CallbackQuery):
    """Користувачі через inline кнопку"""
    logger = logging.getLogger("telegram_bot.handlers.admin")
    logger.info(f"admin_users (inline) від {callback.from_user.id}")
    
    try:
        # Отримуємо дані про користувачів через адмін-сервіс
        bonus_service = get_bonus_service()
        recent_users = await bonus_service.admin_users(10)

        users_text = "👥 <b>Керування користувачами:</b>\n\n"

        if recent_users:
            users_text += "📋 <b>Останні 10 користувачів:</b>\n"
            for user in recent_users:
                name = user.get("name", "Не вказано")
                phone = user.get("phone", "Не вказано")
                user_id = user.get("telegram_user_id", "N/A")
                username = user.get("telegram_username", "")
                created_at = format_date(user.get("created_at", ""))

                phone_status = "📱" if phone != "Не вказано" else "❌"
                users_text += (
                    f"• {phone_status} {user_id} (@{username}) - {created_at}\n"
                )
        else:
            users_text += "📋 Користувачів поки немає\n"

        users_text += "\n🔧 <b>Доступні дії:</b>\n• Переглянути детальну інформацію\n• Заблокувати/розблокувати\n• Експорт списку користувачів"

        # Створюємо inline keyboard
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Детальна статистика", callback_data="admin_users_details"),
                InlineKeyboardButton(text="📱 Без телефонів", callback_data="admin_users_no_phone")
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад до панелі", callback_data="admin_back_to_panel_inline")
            ]
        ])

        await callback.message.edit_text(
            users_text,
            parse_mode="HTML",
            reply_markup=inline_keyboard
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Помилка показу користувачів: {e}")
        await callback.answer("❌ Помилка завантаження", show_alert=True)

import logging
from aiogram import types, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from telegram_bot.middlewares.db import DBSessionMiddleware
from telegram_bot.services import *
from telegram_bot.utils import *
from telegram_bot.data import *

from telegram_bot.handlers.common.dispatcher import dispatch_button_handler
from telegram_bot.handlers.common.permissions import is_admin
from aiogram.utils.markdown import hbold
from telegram_bot.data.keyboards import get_keyboard
from telegram_bot.data.bot_texts import get_text
from telegram_bot.config.redis import cache_user_data, get_cached_user_data
from telegram_bot.utils.logging import log_command, log_button_click, log_message

from telegram_bot.states.phone_state import PhoneState
from telegram_bot.navigation.decorators import button_handler
from telegram_bot.services.bonus_service_universal import get_bonus_service


def register_user_handlers(dp, menu_manager=None):
    """Реєстрація обробників для користувачів"""
    logger = logging.getLogger("telegram_bot.user")
    dp.message.middleware(DBSessionMiddleware())

    @dp.message(CommandStart())
    async def start(message: Message):
        log_command(message, "/start")
        user_id = message.from_user.id
        username = message.from_user.username

        # Кешуємо базову інформацію про користувача в Redis
        user_info = {
            "user_id": user_id,
            "username": username,
            "first_name": message.from_user.first_name,
            "last_name": message.from_user.last_name,
            "last_activity": message.date.isoformat(),
        }
        cache_user_data(user_id, user_info, expire_seconds=3600)  # Кеш на 1 годину

        navigation = dp.get("menu_manager")
        
        # Завжди перевіряємо базу даних на наявність користувача з номером телефону
        bonus_service = get_bonus_service()
        user = await bonus_service.get_user_by_telegram_id(user_id)
        
        has_phone = user and user.get("phone")
        phone = user.get("phone") if user else None
        
        # Оновлюємо кеш стану
        PhoneState.set(user_id, bool(has_phone))

        if not has_phone:
            try:
                bonus_service = get_bonus_service()
                # Створюємо або оновлюємо користувача в таблиці clients
                await bonus_service.upsert_user(
                    user_id,
                    username,
                    first_name=message.from_user.first_name,
                    last_name=message.from_user.last_name,
                    language_code=message.from_user.language_code,
                )
                logger.info(
                    f"Користувач {user_id} ({username}) доданий/оновлений в таблиці clients"
                )
            except Exception as e:
                logger.error(f"Помилка при записі користувача в clients: {e}")
            from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="Поділитись номером", request_contact=True)]
                ],
                resize_keyboard=True,
                one_time_keyboard=True,
            )
            await message.answer(
                get_text("share_phone_prompt")
                or "Будь ласка, поділіться номером телефону для завершення реєстрації:",
                reply_markup=keyboard,
            )
            return

        # Основне меню для зареєстрованих користувачів
        from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

        is_admin_user = is_admin(user_id)
        keyboard_buttons = []
        for btn in get_keyboard("main"):
            if btn["enabled"]:
                keyboard_buttons.append([KeyboardButton(text=btn["text"])])

        if is_admin_user:
            for btn in get_keyboard("admin"):
                if btn["enabled"]:
                    keyboard_buttons.append([KeyboardButton(text=btn["text"])])

        keyboard = ReplyKeyboardMarkup(keyboard=keyboard_buttons, resize_keyboard=True)

        # Використовуємо простий текст замість "welcome_registered" для уникнення плутанини
        welcome_text = get_text("welcome") or f"Головне меню"
        if phone:
            welcome_text += f"\n📱 Телефон: {phone}"

        await message.answer(
            welcome_text,
            reply_markup=keyboard,
        )

    @dp.message()
    async def echo(message: Message, state: FSMContext = None):
        """Основний обробник повідомлень"""
        user_id = message.from_user.id

        # Перевірка FSM стану - якщо користувач в стані FSM, пропускаємо обробку
        if state:
            current_state = await state.get_state()
            if current_state:
                # FSM обробники повинні обробити це повідомлення
                return

        # Перевірка номера телефону
        if message.contact:
            from telegram_bot.handlers.common.share_phone import handle_phone_share

            await handle_phone_share(message)
            return

        # Обробка кнопок меню
        keyboard_buttons = get_keyboard("main")
        if is_admin(user_id):
            keyboard_buttons += get_keyboard("admin")

        for btn in keyboard_buttons:
            if btn["enabled"] and btn["text"] == message.text and btn.get("handler"):
                handler_name = btn["handler"]
                try:
                    log_button_click(message, btn["text"], handler_name)
                    await dispatch_button_handler(handler_name, message)
                    # Видаляємо повідомлення користувача з текстом кнопки
                    try:
                        await message.delete()
                    except:
                        pass
                    return
                except Exception as e:
                    logger.error(f"Помилка при обробці кнопки {handler_name}: {e}")
                    await message.answer(
                        get_text("button_error")
                        or "Сталася помилка при обробці кнопки."
                    )
                    return

        # Відправка невідомого повідомлення
        log_message(message)
        await message.answer(
            get_text("unknown_command")
            or "Невідома команда. Використовуйте кнопки меню."
        )

    @dp.message(F.text == "/redis")
    async def cmd_redis_status(message: Message):
        """Команда для перевірки статусу Redis"""
        log_command(message, "/redis")
        from telegram_bot.config.redis import is_redis_available, get_cached_user_data
        from telegram_bot.utils.logging import get_logging_status

        user_id = message.from_user.id

        # Перевіряємо статус Redis
        redis_status = "✅ Підключено" if is_redis_available() else "❌ Недоступний"

        # Перевіряємо кешовані дані користувача
        cached_data = get_cached_user_data(user_id)
        cache_info = "✅ Знайдено" if cached_data else "❌ Немає даних"

        # Отримуємо статус логування
        log_status = get_logging_status()
        log_info = []
        log_info.append(
            f"📋 Дії користувачів: {'✅' if log_status['user_actions'] else '❌'}"
        )
        log_info.append(f"🔘 Кнопки: {'✅' if log_status['button_clicks'] else '❌'}")
        log_info.append(f"🔧 Команди: {'✅' if log_status['commands'] else '❌'}")
        log_info.append(f"💬 Повідомлення: {'✅' if log_status['messages'] else '❌'}")
        log_info.append(f"🔍 Детальне: {'✅' if log_status['verbose'] else '❌'}")

        response = f"""🔴 **Redis & Логування**

**Redis:** {redis_status}
**Кеш користувача:** {cache_info}

**Налаштування логування:**
{chr(10).join(log_info)}

**Кешовані дані:**
```json
{cached_data if cached_data else "Немає даних"}
```"""

        await message.answer(response, parse_mode="Markdown")

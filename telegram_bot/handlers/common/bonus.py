import logging
from aiogram import types
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from telegram_bot.handlers.common.dispatcher import register_button_handler
from telegram_bot.services.bonus_service_universal import get_bonus_service
from telegram_bot.data.bot_texts import get_text


# Визначення форми станів для процесу додавання/видалення бонусів
class BonusForm(StatesGroup):
    waiting_for_user = State()  # Очікування введення ID користувача
    waiting_for_amount = State()  # Очікування введення кількості бонусів
    waiting_for_reason = State()  # Очікування введення причини
    waiting_for_confirmation = State()  # Очікування підтвердження


# Обробники кнопок
@register_button_handler("add_bonus")
async def add_bonus_start(message: Message, state: FSMContext):
    """
    Обробник для початку процесу додавання бонусів
    """
    from telegram_bot.data.bot_texts import get_text
    logger = logging.getLogger("telegram_bot.handlers.admin_bonus")
    admin_id = message.from_user.id
    logger.info(f"add_bonus_start для admin_id={admin_id}")

    # Встановлюємо операцію в стані
    await state.update_data(operation="add", admin_id=admin_id)

    # Просимо ввести ID користувача
    await message.answer(
        get_text("add_bonus_prompt") or (
            "👤 <b>Додавання бонусів</b>\n\n"
            "Будь ласка, введіть ID користувача, якому потрібно додати бонуси,\n"
            "або пошуковий запит (ім'я, номер телефону) для пошуку користувача.\n\n"
            "<i>Введіть 'скасувати' щоб перервати процес.</i>"
        ),
        parse_mode="HTML",
    )

    # Встановлюємо стан очікування введення ID користувача
    await state.set_state(BonusForm.waiting_for_user)


@register_button_handler("remove_bonus")
async def remove_bonus_start(message: Message, state: FSMContext):
    """
    Обробник для початку процесу видалення бонусів
    """
    from telegram_bot.data.bot_texts import get_text
    logger = logging.getLogger("telegram_bot.handlers.admin_bonus")
    admin_id = message.from_user.id
    logger.info(f"remove_bonus_start для admin_id={admin_id}")

    # Встановлюємо операцію в стані
    await state.update_data(operation="remove", admin_id=admin_id)

    # Просимо ввести ID користувача
    await message.answer(
        get_text("remove_bonus_prompt") or (
            "👤 <b>Списання бонусів</b>\n\n"
            "Будь ласка, введіть ID користувача, у якого потрібно списати бонуси,\n"
            "або пошуковий запит (ім'я, номер телефону) для пошуку користувача.\n\n"
            "<i>Введіть 'скасувати' щоб перервати процес.</i>"
        ),
        parse_mode="HTML",
    )

    # Встановлюємо стан очікування введення ID користувача
    await state.set_state(BonusForm.waiting_for_user)


@register_button_handler("view_bonus_history")
async def view_bonus_history(message: Message):
    """
    Обробник для перегляду історії нарахування бонусів з інформацією про магазини
    """
    logger = logging.getLogger("telegram_bot.handlers.admin_bonus")
    admin_id = message.from_user.id
    logger.info(f"view_bonus_history для admin_id={admin_id}")

    try:
        bonus_service = get_bonus_service()
        history = await bonus_service.get_bonus_history(limit=15)

        if not history:
            await message.answer(
                "📝 <b>Історія бонусів</b>\n\n" "Історія бонусів порожня.",
                parse_mode="HTML",
                reply_markup=types.ReplyKeyboardMarkup(
                    keyboard=[[types.KeyboardButton(text="⬅️ Назад до адмін-панелі")]],
                    resize_keyboard=True,
                ),
            )
            return

        # Формуємо текст повідомлення з розширеною інформацією
        history_text = "📝 <b>Останні операції з бонусами:</b>\n\n"

        for i, item in enumerate(history, 1):
            user_id = item.get("client_id", "N/A")
            username = item.get("username", "")
            first_name = item.get("first_name", "")
            amount = item.get("amount", 0)
            description = item.get("description", "Не вказано")
            
            # Форматуємо дату
            from telegram_bot.utils.datetime_helpers import format_datetime
            created_at = format_datetime(item.get("created_at", ""))
            
            # Символ операції
            operation = "➕" if amount > 0 else "➖"
            
            # Формуємо ім'я користувача
            user_display = f"{first_name} (@{username})" if username else first_name or f"ID: {user_id}"
            
            # Основна інформація про транзакцію
            history_text += (
                f"{i}. {operation} <b>{user_display}</b>: {abs(amount)} бонусів\n"
                f"   📅 {created_at}\n"
            )
            
            # Додаємо інформацію про магазин якщо є
            if item.get("store_name"):
                history_text += f"   🏪 {item['store_name']}\n"
                if item.get("store_address"):
                    # Скорочуємо адресу для компактності
                    address = item['store_address']
                    if len(address) > 40:
                        address = address[:37] + "..."
                    history_text += f"   📍 {address}\n"
            
            # Додаємо інформацію про чек якщо є
            if item.get("receipt_number"):
                receipt_info = f"   🧾 Чек #{item['receipt_number']}"
                if item.get("receipt_total"):
                    receipt_info += f" на {item['receipt_total']:.2f} грн"
                history_text += receipt_info + "\n"
            
            # Додаємо опис якщо це не покупка в магазині
            if not item.get("store_name") and description != "Не вказано":
                history_text += f"   📝 {description}\n"
            
            history_text += "\n"

            # Обмежуємо довжину повідомлення
            if len(history_text) > 3500:
                history_text += "...\n<i>Показано лише останні записи</i>"
                break

        # Відправляємо повідомлення з історією
        await message.answer(
            history_text,
            parse_mode="HTML",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[[types.KeyboardButton(text="⬅️ Назад до адмін-панелі")]],
                resize_keyboard=True,
            ),
        )

    except Exception as e:
        logger.error(f"Помилка при отриманні історії бонусів: {e}")
        await message.answer(
            f"❌ Помилка при отриманні історії бонусів: {e}",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[[types.KeyboardButton(text="⬅️ Назад до адмін-панелі")]],
                resize_keyboard=True,
            ),
        )

        for i, item in enumerate(history, 1):
            user_id = item.get("user_id", "N/A")
            change = item.get("change", 0)  # Використовуємо 'change' замість 'amount'
            description = item.get(
                "description", "Не вказано"
            )  # Використовуємо 'description' замість 'reason'
            from telegram_bot.utils.datetime_helpers import format_datetime

            created_at = format_datetime(item.get("created_at", ""))  # Форматуємо дату
            operation = "➕" if change > 0 else "➖"

            history_text += (
                f"{i}. {operation} <b>User {user_id}</b>: {abs(change)} бонусів\n"
            )
            history_text += f"   📅 {created_at}\n"
            history_text += f"   📝 {description}\n\n"

            # Обмежуємо довжину повідомлення
            if len(history_text) > 3000:
                history_text += "...\n<i>Показано лише останні записи</i>"
                break

        # Відправляємо повідомлення з історією
        await message.answer(
            history_text,
            parse_mode="HTML",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[[types.KeyboardButton(text="⬅️ Назад до адмін-панелі")]],
                resize_keyboard=True,
            ),
        )

    except Exception as e:
        logger.error(f"Помилка при отриманні історії бонусів: {e}")
        await message.answer(
            f"❌ Помилка при отриманні історії бонусів: {e}",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[[types.KeyboardButton(text="⬅️ Назад до адмін-панелі")]],
                resize_keyboard=True,
            ),
        )


# Обробники станів форми
async def process_user_input(message: Message, state: FSMContext):
    """
    Обробник введення ID користувача або пошукового запиту
    """
    logger = logging.getLogger("telegram_bot.handlers.admin_bonus")

    # Отримуємо текст повідомлення
    text = message.text.strip()

    # Перевіряємо на скасування
    if text.lower() == "скасувати":
        await state.clear()
        await message.answer(
            "❌ Операцію скасовано.",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[[types.KeyboardButton(text="⬅️ Назад до адмін-панелі")]],
                resize_keyboard=True,
            ),
        )
        return

    # Перевіряємо, чи є введений текст числом (ID користувача)
    if text.isdigit():
        user_id = int(text)
        bonus_service = get_bonus_service()
        user = await bonus_service.get_user_by_id(user_id)

        if user:
            # Зберігаємо ID користувача в стані
            await state.update_data(
                user_id=user_id, username=user.get("username", "N/A")
            )

            # Отримуємо поточний баланс користувача
            balance = await bonus_service.get_user_balance(user_id)

            # Отримуємо тип операції зі стану
            state_data = await state.get_data()
            operation = state_data.get("operation", "add")

            # Формуємо повідомлення в залежності від операції
            if operation == "add":
                await message.answer(
                    f"👤 <b>Користувач знайдений:</b>\n"
                    f"ID: {user_id}\n"
                    f"Ім'я: {user.get('username', 'Не вказано')}\n"
                    f"Телефон: {user.get('phone', 'Не вказано')}\n"
                    f"Поточний баланс: {balance} бонусів\n\n"
                    f"Введіть кількість бонусів для додавання (ціле число):\n\n"
                    f"<i>Введіть 'скасувати' щоб перервати процес.</i>",
                    parse_mode="HTML",
                )
            else:  # remove
                await message.answer(
                    f"👤 <b>Користувач знайдений:</b>\n"
                    f"ID: {user_id}\n"
                    f"Ім'я: {user.get('username', 'Не вказано')}\n"
                    f"Телефон: {user.get('phone', 'Не вказано')}\n"
                    f"Поточний баланс: {balance} бонусів\n\n"
                    f"Введіть кількість бонусів для списання (ціле число):\n\n"
                    f"<i>Введіть 'скасувати' щоб перервати процес.</i>",
                    parse_mode="HTML",
                )  # Переходимо до наступного стану
            await state.set_state(BonusForm.waiting_for_amount)
        else:
            await message.answer(
                f"❌ Користувача з ID {user_id} не знайдено.\n"
                f"Спробуйте ввести інший ID або пошуковий запит.\n\n"
                f"<i>Введіть 'скасувати' щоб перервати процес.</i>",
                parse_mode="HTML",
            )
    else:
        # Пошук користувачів за запитом
        bonus_service = get_bonus_service()
        users = await bonus_service.search_users(text)

        if users:
            if len(users) == 1:
                # Якщо знайдено лише одного користувача, вибираємо його автоматично
                user = users[0]
                user_id = user.get("user_id")

                # Зберігаємо ID користувача в стані
                await state.update_data(
                    user_id=user_id, username=user.get("username", "N/A")
                )

                # Отримуємо поточний баланс користувача
                balance = await bonus_service.get_user_balance(user_id)

                # Отримуємо тип операції зі стану
                state_data = await state.get_data()
                operation = state_data.get("operation", "add")

                # Формуємо повідомлення в залежності від операції
                if operation == "add":
                    await message.answer(
                        f"👤 <b>Користувач знайдений:</b>\n"
                        f"ID: {user_id}\n"
                        f"Ім'я: {user.get('username', 'Не вказано')}\n"
                        f"Телефон: {user.get('phone', 'Не вказано')}\n"
                        f"Поточний баланс: {balance} бонусів\n\n"
                        f"Введіть кількість бонусів для додавання (ціле число):\n\n"
                        f"<i>Введіть 'скасувати' щоб перервати процес.</i>",
                        parse_mode="HTML",
                    )
                else:  # remove
                    await message.answer(
                        f"👤 <b>Користувач знайдений:</b>\n"
                        f"ID: {user_id}\n"
                        f"Ім'я: {user.get('username', 'Не вказано')}\n"
                        f"Телефон: {user.get('phone', 'Не вказано')}\n"
                        f"Поточний баланс: {balance} бонусів\n\n"
                        f"Введіть кількість бонусів для списання (ціле число):\n\n"
                        f"<i>Введіть 'скасувати' щоб перервати процес.</i>",
                        parse_mode="HTML",
                    )  # Переходимо до наступного стану
                await state.set_state(BonusForm.waiting_for_amount)
            else:
                # Якщо знайдено кілька користувачів, показуємо список
                users_text = "👥 <b>Знайдено кілька користувачів:</b>\n\n"

                for user in users:
                    user_id = user.get("user_id", "N/A")
                    username = user.get("username", "Не вказано")
                    phone = user.get("phone", "Не вказано")

                    users_text += f"ID: {user_id}\n"
                    users_text += f"Ім'я: {username}\n"
                    users_text += f"Телефон: {phone}\n\n"

                users_text += (
                    "Будь ласка, введіть ID користувача з наведеного списку.\n\n"
                )
                users_text += "<i>Введіть 'скасувати' щоб перервати процес.</i>"

                await message.answer(
                    users_text,
                    parse_mode="HTML",
                )
        else:
            await message.answer(
                f"❌ Користувачів за запитом '{text}' не знайдено.\n"
                f"Спробуйте ввести інший запит.\n\n"
                f"<i>Введіть 'скасувати' щоб перервати процес.</i>",
                parse_mode="HTML",
            )


async def process_amount_input(message: Message, state: FSMContext):
    """
    Обробник введення кількості бонусів
    """
    logger = logging.getLogger("telegram_bot.handlers.admin_bonus")

    # Отримуємо текст повідомлення
    text = message.text.strip()

    # Перевіряємо на скасування
    if text.lower() == "скасувати":
        await state.clear()
        await message.answer(
            "❌ Операцію скасовано.",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[[types.KeyboardButton(text="⬅️ Назад до адмін-панелі")]],
                resize_keyboard=True,
            ),
        )
        return

    # Перевіряємо, чи є введений текст числом
    if text.isdigit() and int(text) > 0:
        amount = int(text)

        # Зберігаємо кількість бонусів в стані
        await state.update_data(amount=amount)

        # Отримуємо тип операції зі стану
        state_data = await state.get_data()
        operation = state_data.get("operation", "add")
        user_id = state_data.get("user_id")
        username = state_data.get("username", "N/A")

        # Перевіряємо чи достатньо бонусів для списання
        if operation == "remove":
            bonus_service = get_bonus_service()
            balance = await bonus_service.get_user_balance(user_id)
            if balance < amount:
                await message.answer(
                    f"❌ У користувача недостатньо бонусів для списання.\n"
                    f"Поточний баланс: {balance}\n"
                    f"Ви намагаєтесь списати: {amount}\n\n"
                    f"Будь ласка, введіть меншу кількість бонусів:\n\n"
                    f"<i>Введіть 'скасувати' щоб перервати процес.</i>",
                    parse_mode="HTML",
                )
                return

        # Просимо ввести причину операції
        if operation == "add":
            await message.answer(
                f"📝 <b>Додавання {amount} бонусів для користувача {username}</b>\n\n"
                f"Будь ласка, введіть причину додавання бонусів:\n\n"
                f"<i>Введіть 'скасувати' щоб перервати процес.</i>",
                parse_mode="HTML",
            )
        else:  # remove
            await message.answer(
                f"📝 <b>Списання {amount} бонусів у користувача {username}</b>\n\n"
                f"Будь ласка, введіть причину списання бонусів:\n\n"
                f"<i>Введіть 'скасувати' щоб перервати процес.</i>",
                parse_mode="HTML",
            )  # Переходимо до наступного стану
        await state.set_state(BonusForm.waiting_for_reason)
    else:
        await message.answer(
            f"❌ Будь ласка, введіть додатне ціле число.\n\n"
            f"<i>Введіть 'скасувати' щоб перервати процес.</i>",
            parse_mode="HTML",
        )


async def process_reason_input(message: Message, state: FSMContext):
    """
    Обробник введення причини операції
    """
    logger = logging.getLogger("telegram_bot.handlers.admin_bonus")

    # Отримуємо текст повідомлення
    text = message.text.strip()

    # Перевіряємо на скасування
    if text.lower() == "скасувати":
        await state.clear()
        await message.answer(
            "❌ Операцію скасовано.",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[[types.KeyboardButton(text="⬅️ Назад до адмін-панелі")]],
                resize_keyboard=True,
            ),
        )
        return

    # Зберігаємо причину в стані
    await state.update_data(reason=text)

    # Отримуємо дані зі стану
    state_data = await state.get_data()
    operation = state_data.get("operation", "add")
    user_id = state_data.get("user_id")
    username = state_data.get("username", "N/A")
    amount = state_data.get("amount")

    # Формуємо повідомлення підтвердження
    if operation == "add":
        confirmation_text = (
            f"✅ <b>Підтвердження операції:</b>\n\n"
            f"Ви хочете додати <b>{amount}</b> бонусів користувачу:\n"
            f"ID: {user_id}\n"
            f"Ім'я: {username}\n\n"
            f"Причина: {text}\n\n"
            f"Для підтвердження введіть 'так'.\n"
            f"Для скасування введіть 'ні'."
        )
    else:  # remove
        confirmation_text = (
            f"✅ <b>Підтвердження операції:</b>\n\n"
            f"Ви хочете списати <b>{amount}</b> бонусів у користувача:\n"
            f"ID: {user_id}\n"
            f"Ім'я: {username}\n\n"
            f"Причина: {text}\n\n"
            f"Для підтвердження введіть 'так'.\n"
            f"Для скасування введіть 'ні'."
        )

    await message.answer(
        confirmation_text,
        parse_mode="HTML",
    )

    # Переходимо до стану очікування підтвердження
    await state.set_state(BonusForm.waiting_for_confirmation)


async def process_confirmation(message: Message, state: FSMContext):
    """
    Обробник підтвердження операції
    """
    logger = logging.getLogger("telegram_bot.handlers.admin_bonus")

    # Отримуємо текст повідомлення
    text = message.text.strip().lower()

    # Перевіряємо підтвердження
    if text == "так":
        # Отримуємо дані зі стану
        state_data = await state.get_data()
        operation = state_data.get("operation", "add")
        user_id = state_data.get("user_id")
        amount = state_data.get("amount")
        reason = state_data.get("reason")
        admin_id = state_data.get("admin_id")

        try:
            # Виконуємо операцію
            bonus_service = get_bonus_service()
            if operation == "add":
                success = await bonus_service.add_bonus(
                    user_id=user_id, amount=amount, reason=reason, admin_id=admin_id
                )

                if success:
                    # Отримуємо новий баланс
                    new_balance = await bonus_service.get_user_balance(user_id)

                    await message.answer(
                        f"✅ <b>Бонуси успішно додано!</b>\n\n"
                        f"Користувачу ID {user_id} додано {amount} бонусів.\n"
                        f"Новий баланс: {new_balance} бонусів.\n\n"
                        f"Операцію виконано успішно!",
                        parse_mode="HTML",
                        reply_markup=types.ReplyKeyboardMarkup(
                            keyboard=[
                                [types.KeyboardButton(text="⬅️ Назад до адмін-панелі")]
                            ],
                            resize_keyboard=True,
                        ),
                    )
                else:
                    await message.answer(
                        f"❌ Помилка при додаванні бонусів.\n\n"
                        f"Будь ласка, спробуйте ще раз або зверніться до технічної підтримки.",
                        reply_markup=types.ReplyKeyboardMarkup(
                            keyboard=[
                                [types.KeyboardButton(text="⬅️ Назад до адмін-панелі")]
                            ],
                            resize_keyboard=True,
                        ),
                    )
            else:  # remove
                success = await bonus_service.remove_bonus(
                    user_id=user_id, amount=amount, reason=reason, admin_id=admin_id
                )

                if success:
                    # Отримуємо новий баланс
                    new_balance = await bonus_service.get_user_balance(user_id)

                    await message.answer(
                        f"✅ <b>Бонуси успішно списано!</b>\n\n"
                        f"У користувача ID {user_id} списано {amount} бонусів.\n"
                        f"Новий баланс: {new_balance} бонусів.\n\n"
                        f"Операцію виконано успішно!",
                        parse_mode="HTML",
                        reply_markup=types.ReplyKeyboardMarkup(
                            keyboard=[
                                [types.KeyboardButton(text="⬅️ Назад до адмін-панелі")]
                            ],
                            resize_keyboard=True,
                        ),
                    )
                else:
                    await message.answer(
                        f"❌ Помилка при списанні бонусів.\n\n"
                        f"Будь ласка, спробуйте ще раз або зверніться до технічної підтримки.",
                        reply_markup=types.ReplyKeyboardMarkup(
                            keyboard=[
                                [types.KeyboardButton(text="⬅️ Назад до адмін-панелі")]
                            ],
                            resize_keyboard=True,
                        ),
                    )
        except Exception as e:
            logger.error(f"Помилка при виконанні операції з бонусами: {e}")
            await message.answer(
                f"❌ Помилка при виконанні операції: {str(e)}",
                reply_markup=types.ReplyKeyboardMarkup(
                    keyboard=[[types.KeyboardButton(text="⬅️ Назад до адмін-панелі")]],
                    resize_keyboard=True,
                ),
            )
    else:
        # Скасування операції
        await message.answer(
            "❌ Операцію скасовано.",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[[types.KeyboardButton(text="⬅️ Назад до адмін-панелі")]],
                resize_keyboard=True,
            ),
        )

    # Завершуємо форму
    await state.clear()


# Функція для реєстрації обробників станів
def register_admin_bonus_handlers(dp):
    """
    Реєструє обробники станів форми в диспетчері
    """
    dp.message.register(process_user_input, BonusForm.waiting_for_user)
    dp.message.register(process_amount_input, BonusForm.waiting_for_amount)
    dp.message.register(process_reason_input, BonusForm.waiting_for_reason)
    dp.message.register(process_confirmation, BonusForm.waiting_for_confirmation)

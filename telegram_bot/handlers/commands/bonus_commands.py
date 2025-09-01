"""
Обробники команд для роботи з бонусною системою
"""

import logging
import re
from aiogram import types
from aiogram.types import Message
from aiogram.filters import Command
from telegram_bot.services.bonus_service_universal import get_bonus_service

logger = logging.getLogger("telegram_bot.bonus_commands")


async def cmd_bonus(message: Message):
    """Команда /bonus [client_id|phone|name] - показати інформацію про бонуси клієнта"""
    logger.info(f"cmd_bonus від {message.from_user.id}: {message.text}")

    # Витягуємо аргумент з команди
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []

    if not args:
        await message.answer(
            "🔍 <b>Пошук клієнта для перегляду бонусів</b>\n\n"
            "Використання: <code>/bonus [ID|телефон|ім'я]</code>\n\n"
            "Приклади:\n"
            "• <code>/bonus 13763</code> - за ID\n"
            "• <code>/bonus +380671234567</code> - за телефоном\n"
            "• <code>/bonus Іван</code> - за ім'ям\n",
            parse_mode="HTML",
        )
        return

    query = " ".join(args)
    bonus_service = get_bonus_service()

    try:
        # Спробуємо спочатку як ID
        if query.isdigit():
            client_id = int(query)
            user_data = await bonus_service.get_user_by_id(client_id)

            if user_data:
                balance = await bonus_service.get_user_balance(client_id)
                await message.answer(
                    f"🧑‍💼 <b>Клієнт #{client_id}</b>\n"
                    f"📛 <b>Ім'я:</b> {user_data.get('name', 'Не вказано')}\n"
                    f"📞 <b>Телефон:</b> {user_data.get('phone', 'Не вказано')}\n"
                    f"💰 <b>Баланс:</b> {balance:.2f} грн\n\n"
                    f"Для повної історії: <code>/history {client_id}</code>",
                    parse_mode="HTML",
                )
                return

        # Якщо не ID, шукаємо за запитом
        search_results = await bonus_service.search_users(query, limit=5)

        if not search_results:
            await message.answer(f"❌ Клієнтів за запитом '{query}' не знайдено")
            return

        if len(search_results) == 1:
            # Знайдений один клієнт - показуємо інформацію
            client = search_results[0]
            client_id = client["client_id"]
            balance = await bonus_service.get_user_balance(client_id)

            await message.answer(
                f"🧑‍💼 <b>Клієнт #{client_id}</b>\n"
                f"📛 <b>Ім'я:</b> {client.get('name', 'Не вказано')}\n"
                f"📞 <b>Телефон:</b> {client.get('phone', 'Не вказано')}\n"
                f"💰 <b>Баланс:</b> {balance:.2f} грн\n\n"
                f"Для повної історії: <code>/history {client_id}</code>",
                parse_mode="HTML",
            )
        else:
            # Знайдено кілька клієнтів - показуємо список
            response = f"🔍 <b>Знайдено {len(search_results)} клієнтів за запитом '{query}':</b>\n\n"

            for client in search_results:
                client_id = client["client_id"]
                name = client.get("name", "Не вказано")
                phone = client.get("phone", "Не вказано")
                balance = client.get("bonus", 0) / 100.0  # Конвертуємо з копійок

                response += f"👤 <b>#{client_id}</b> - {name}\n"
                response += f"📞 {phone} | 💰 {balance:.2f} грн\n"
                response += f"<code>/bonus {client_id}</code> - детальна інформація\n\n"

            await message.answer(response, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Помилка в cmd_bonus: {e}")
        await message.answer("❌ Сталася помилка при пошуку клієнта")


async def cmd_history(message: Message):
    """Команда /history [client_id|phone|name] - показати повну історію бонусів клієнта"""
    logger.info(f"cmd_history від {message.from_user.id}: {message.text}")

    # Витягуємо аргумент з команди
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []

    if not args:
        await message.answer(
            "📋 <b>Історія бонусів клієнта</b>\n\n"
            "Використання: <code>/history [ID|телефон|ім'я]</code>\n\n"
            "Приклади:\n"
            "• <code>/history 13763</code> - за ID\n"
            "• <code>/history +380671234567</code> - за телефоном\n"
            "• <code>/history Іван</code> - за ім'ям\n",
            parse_mode="HTML",
        )
        return

    query = " ".join(args)
    bonus_service = get_bonus_service()

    try:
        client_id = None

        # Спробуємо спочатку як ID
        if query.isdigit():
            client_id = int(query)
            user_data = await bonus_service.get_user_by_id(client_id)
            if not user_data:
                await message.answer(f"❌ Клієнт #{client_id} не знайдений")
                return
        else:
            # Шукаємо за запитом
            search_results = await bonus_service.search_users(query, limit=5)

            if not search_results:
                await message.answer(f"❌ Клієнтів за запитом '{query}' не знайдено")
                return

            if len(search_results) == 1:
                client_id = search_results[0]["client_id"]
            else:
                # Кілька результатів - показуємо список
                response = f"🔍 <b>Знайдено {len(search_results)} клієнтів:</b>\n\n"
                for client in search_results:
                    response += f"👤 <b>#{client['client_id']}</b> - {client.get('name', 'Не вказано')}\n"
                    response += f"📞 {client.get('phone', 'Не вказано')}\n"
                    response += f"<code>/history {client['client_id']}</code>\n\n"

                await message.answer(response, parse_mode="HTML")
                return

        # Отримуємо повну історію
        if client_id:
            await message.answer("⏳ Генерую історію бонусів...")

            history = await bonus_service.get_user_history(client_id, limit=10)

            # Розбиваємо на частини, якщо текст занадто довгий
            if len(history) > 4000:
                parts = []
                lines = history.split("\n")
                current_part = ""

                for line in lines:
                    if len(current_part + line + "\n") > 4000:
                        parts.append(current_part)
                        current_part = line + "\n"
                    else:
                        current_part += line + "\n"

                if current_part:
                    parts.append(current_part)

                # Відправляємо частинами
                for i, part in enumerate(parts):
                    if i == 0:
                        await message.answer(part, parse_mode="HTML")
                    else:
                        await message.answer(
                            f"📄 <b>Продовження ({i+1}/{len(parts)})...</b>\n\n{part}",
                            parse_mode="HTML",
                        )
            else:
                await message.answer(history, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Помилка в cmd_history: {e}")
        await message.answer("❌ Сталася помилка при отриманні історії")


async def cmd_search(message: Message):
    """Команда /search [query] - пошук клієнтів"""
    logger.info(f"cmd_search від {message.from_user.id}: {message.text}")

    # Витягуємо аргумент з команди
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []

    if not args:
        await message.answer(
            "🔍 <b>Пошук клієнтів</b>\n\n"
            "Використання: <code>/search [запит]</code>\n\n"
            "Приклади:\n"
            "• <code>/search Іван</code> - за ім'ям\n"
            "• <code>/search 380671234</code> - за частиною телефону\n"
            "• <code>/search Петренко</code> - за прізвищем\n",
            parse_mode="HTML",
        )
        return

    query = " ".join(args)
    bonus_service = get_bonus_service()

    try:
        await message.answer(f"🔍 Шукаю клієнтів за запитом '{query}'...")

        search_results = await bonus_service.search_users(query, limit=15)

        if not search_results:
            await message.answer(f"❌ Клієнтів за запитом '{query}' не знайдено")
            return

        response = f"🔍 <b>Знайдено {len(search_results)} клієнтів:</b>\n\n"

        for client in search_results:
            client_id = client["client_id"]
            name = client.get("name", "Не вказано")
            phone = client.get("phone", "Не вказано")
            balance = client.get("bonus", 0) / 100.0  # Конвертуємо з копійок

            response += f"👤 <b>#{client_id}</b> - {name}\n"
            response += f"📞 {phone} | 💰 {balance:.2f} грн\n"
            response += f"<code>/bonus {client_id}</code> | <code>/history {client_id}</code>\n\n"

        # Розбиваємо на частини, якщо занадто довго
        if len(response) > 4000:
            parts = []
            lines = response.split("\n")
            current_part = (
                f"🔍 <b>Знайдено {len(search_results)} клієнтів (частина 1):</b>\n\n"
            )

            for line in lines[2:]:  # Пропускаємо заголовок
                if len(current_part + line + "\n") > 4000:
                    parts.append(current_part)
                    current_part = f"📄 <b>Продовження...</b>\n\n{line}\n"
                else:
                    current_part += line + "\n"

            if current_part:
                parts.append(current_part)

            for part in parts:
                await message.answer(part, parse_mode="HTML")
        else:
            await message.answer(response, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Помилка в cmd_search: {e}")
        await message.answer("❌ Сталася помилка при пошуку клієнтів")


def register_bonus_commands(dp):
    """Реєстрація команд для роботи з бонусами"""
    dp.message.register(cmd_bonus, Command("bonus"))
    dp.message.register(cmd_history, Command("history"))
    dp.message.register(cmd_search, Command("search"))

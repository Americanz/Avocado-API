"""
Сервіс для роботи з бонусною системою PostgreSQL
Інтегрований з нашою системою transaction_bonus та clients
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import create_engine, text
from telegram_bot.services.bonus_service_universal import AbstractBonusService


class PostgreSQLBonusService(AbstractBonusService):
    """Сервіс для роботи з бонусною системою PostgreSQL"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.logger = logging.getLogger("telegram_bot.postgresql_bonus")

    def format_client_balance(self, balance_kopecks):
        """Форматування балансу клієнта (конвертація з копійок в гривні)"""
        if balance_kopecks is not None:
            return f"{(balance_kopecks / 100):.2f}"
        return "0.00"

    def format_datetime(self, dt):
        """Форматування дати та часу"""
        if dt:
            return dt.strftime("%d.%m.%Y %H:%M")
        return "N/A"

    async def get_user_by_telegram_id(self, telegram_user_id: int) -> Optional[Dict]:
        """Отримати клієнта за Telegram ID"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text(
                        """
                        SELECT client_id, firstname, lastname, patronymic, phone, bonus, created_at, updated_at,
                               telegram_user_id, telegram_username, telegram_first_name, telegram_last_name
                        FROM clients
                        WHERE telegram_user_id = :telegram_user_id
                    """
                    ),
                    {"telegram_user_id": telegram_user_id},
                ).fetchone()

                if result:
                    # Формуємо повне ім'я
                    name_parts = []
                    if result[1]:  # firstname
                        name_parts.append(result[1])
                    if result[2]:  # lastname
                        name_parts.append(result[2])
                    if result[3]:  # patronymic
                        name_parts.append(result[3])

                    full_name = " ".join(name_parts) if name_parts else "Не вказано"

                    return {
                        "client_id": result[0],
                        "name": full_name,
                        "firstname": result[1],
                        "lastname": result[2],
                        "patronymic": result[3],
                        "phone": result[4],
                        "bonus": result[5],
                        "created_at": result[6],
                        "updated_at": result[7],
                        "telegram_user_id": result[8],
                        "telegram_username": result[9],
                        "telegram_first_name": result[10],
                        "telegram_last_name": result[11],
                    }
                return None
        except Exception as e:
            self.logger.error(
                f"Помилка отримання клієнта за Telegram ID {telegram_user_id}: {e}"
            )
            return None

    async def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Отримати клієнта за ID (спочатку як client_id, потім як telegram_user_id)"""
        try:
            with self.engine.connect() as conn:
                # Спочатку шукаємо за client_id (для Poster клієнтів)
                result = conn.execute(
                    text(
                        """
                        SELECT client_id, firstname, lastname, patronymic, phone, bonus, created_at, updated_at,
                               telegram_user_id, telegram_username, telegram_first_name, telegram_last_name
                        FROM clients
                        WHERE client_id = :client_id
                    """
                    ),
                    {"client_id": user_id},
                ).fetchone()

                # Якщо не знайшли за client_id, шукаємо за telegram_user_id
                if not result:
                    result = conn.execute(
                        text(
                            """
                            SELECT client_id, firstname, lastname, patronymic, phone, bonus, created_at, updated_at,
                                   telegram_user_id, telegram_username, telegram_first_name, telegram_last_name
                            FROM clients
                            WHERE telegram_user_id = :telegram_user_id
                        """
                        ),
                        {"telegram_user_id": user_id},
                    ).fetchone()

                if result:
                    # Формуємо повне ім'я
                    name_parts = []
                    if result[1]:  # firstname
                        name_parts.append(result[1])
                    if result[2]:  # lastname
                        name_parts.append(result[2])
                    if result[3]:  # patronymic
                        name_parts.append(result[3])

                    full_name = " ".join(name_parts) if name_parts else "Не вказано"

                    return {
                        "client_id": result[0],  # може бути NULL для Telegram користувачів
                        "name": full_name,
                        "firstname": result[1],
                        "lastname": result[2],
                        "patronymic": result[3],
                        "phone": result[4],
                        "bonus": result[5],
                        "created_at": result[6],
                        "updated_at": result[7],
                        "telegram_user_id": result[8],
                        "telegram_username": result[9],
                        "telegram_first_name": result[10],
                        "telegram_last_name": result[11],
                    }
                return None
        except Exception as e:
            self.logger.error(f"Помилка отримання клієнта {user_id}: {e}")
            return None

    async def search_users(self, query: str, limit: int = 10) -> List[Dict]:
        """Пошук клієнтів за іменем або телефоном"""
        try:
            with self.engine.connect() as conn:
                # Очищаємо телефон від всіх символів крім цифр
                clean_query = "".join(filter(str.isdigit, query))

                results = conn.execute(
                    text(
                        """
                        SELECT client_id, firstname, lastname, patronymic, phone, bonus, created_at
                        FROM clients
                        WHERE
                            (LOWER(CONCAT(firstname, ' ', lastname, ' ', COALESCE(patronymic, ''))) LIKE LOWER(:name_query)) OR
                            (LOWER(firstname) LIKE LOWER(:name_query)) OR
                            (LOWER(lastname) LIKE LOWER(:name_query)) OR
                            phone_number LIKE :phone_query OR
                            REPLACE(REPLACE(REPLACE(phone, '+', ''), ' ', ''), '-', '') LIKE :phone_query
                        ORDER BY
                            CASE
                                WHEN LOWER(CONCAT(firstname, ' ', lastname)) = LOWER(:exact_name) THEN 1
                                WHEN LOWER(firstname) LIKE LOWER(:name_starts) THEN 2
                                WHEN LOWER(lastname) LIKE LOWER(:name_starts) THEN 3
                                ELSE 4
                            END,
                            lastname, firstname
                        LIMIT :limit
                    """
                    ),
                    {
                        "name_query": f"%{query}%",
                        "phone_query": f"%{clean_query}%",
                        "exact_name": query,
                        "name_starts": f"{query}%",
                        "limit": limit,
                    },
                ).fetchall()

                users = []
                for result in results:
                    # Формуємо повне ім'я
                    name_parts = []
                    if result[1]:  # firstname
                        name_parts.append(result[1])
                    if result[2]:  # lastname
                        name_parts.append(result[2])
                    if result[3]:  # patronymic
                        name_parts.append(result[3])

                    full_name = " ".join(name_parts) if name_parts else "Не вказано"

                    users.append(
                        {
                            "client_id": result[0],
                            "name": full_name,
                            "firstname": result[1],
                            "lastname": result[2],
                            "patronymic": result[3],
                            "phone": result[4],
                            "bonus": result[5],
                            "created_at": result[6],
                        }
                    )

                return users
        except Exception as e:
            self.logger.error(f"Помилка пошуку клієнтів '{query}': {e}")
            return []

    async def get_user_balance(self, user_id: int) -> Optional[float]:
        """Отримати баланс клієнта в гривнях (шукаємо за client_id або telegram_user_id)"""
        try:
            with self.engine.connect() as conn:
                # Спочатку шукаємо за client_id
                result = conn.execute(
                    text("SELECT bonus FROM clients WHERE client_id = :client_id"),
                    {"client_id": user_id},
                ).scalar()

                # Якщо не знайшли за client_id, шукаємо за telegram_user_id
                if result is None:
                    result = conn.execute(
                        text("SELECT bonus FROM clients WHERE telegram_user_id = :telegram_user_id"),
                        {"telegram_user_id": user_id},
                    ).scalar()

                if result is not None:
                    return float(result) / 100.0  # Конвертуємо з копійок в гривні
                return None
        except Exception as e:
            self.logger.error(f"Помилка отримання балансу {user_id}: {e}")
            return None

    async def user_balance_exists(self, user_id: int) -> bool:
        """Перевірити, чи існує клієнт"""
        user = await self.get_user_by_id(user_id)
        return user is not None

    async def get_user_history(self, user_id: int, limit: int = 10) -> str:
        """Отримати повну історію бонусів клієнта (як в check_client_bonus.py)"""
        try:
            with self.engine.connect() as conn:
                # 1. Базова інформація про клієнта
                client_info = conn.execute(
                    text(
                        """
                        SELECT client_id, firstname, lastname, patronymic, phone, bonus, created_at, updated_at
                        FROM clients
                        WHERE client_id = :client_id OR telegram_user_id = :telegram_user_id
                    """
                    ),
                    {"client_id": user_id, "telegram_user_id": user_id},
                ).fetchone()

                if not client_info:
                    return f"❌ Клієнт #{user_id} не знайдений"

                # Формуємо повне ім'я
                name_parts = []
                if client_info[1]:  # firstname
                    name_parts.append(client_info[1])
                if client_info[2]:  # lastname
                    name_parts.append(client_info[2])
                if client_info[3]:  # patronymic
                    name_parts.append(client_info[3])
                
                full_name = " ".join(name_parts) if name_parts else "Не вказано"

                # 2. Статистика бонусних операцій
                bonus_stats = conn.execute(
                    text(
                        """
                        SELECT
                            operation_type,
                            COUNT(*) as count,
                            SUM(amount) as total_amount,
                            MAX(processed_at) as last_operation
                        FROM transaction_bonus
                        WHERE client_id = :client_id
                        GROUP BY operation_type
                        ORDER BY operation_type
                    """
                    ),
                    {"client_id": user_id},
                ).fetchall()

                # 3. Останні бонусні операції
                bonus_history = conn.execute(
                    text(
                        """
                        SELECT
                            transaction_id,
                            operation_type,
                            amount,
                            balance_before,
                            balance_after,
                            description,
                            processed_at
                        FROM transaction_bonus
                        WHERE client_id = :client_id
                        ORDER BY processed_at DESC
                        LIMIT :limit
                    """
                    ),
                    {"client_id": user_id, "limit": limit},
                ).fetchall()

                # 4. Останні транзакції з товарами
                transactions = conn.execute(
                    text(
                        """
                        SELECT
                            t.transaction_id,
                            t.sum,
                            t.bonus,
                            t.payed_bonus,
                            t.date_close,
                            s.name as spot_name,
                            STRING_AGG(
                                DISTINCT p.product_name || ' (' || tp.count || ' шт. × ' || tp.price || ' грн)',
                                ', '
                                ORDER BY p.product_name || ' (' || tp.count || ' шт. × ' || tp.price || ' грн)'
                            ) as products_list
                        FROM transactions t
                        LEFT JOIN spots s ON t.spot = s.spot_id
                        LEFT JOIN transaction_products tp ON t.transaction_id = tp.transaction_id
                        LEFT JOIN products p ON tp.product = p.poster_product_id
                        WHERE t.client_id = :client_id
                        AND t.date_close IS NOT NULL
                        GROUP BY t.transaction_id, t.sum, t.bonus, t.payed_bonus, t.date_close, s.name
                        ORDER BY t.date_close DESC
                        LIMIT 5
                    """
                    ),
                    {"client_id": user_id},
                ).fetchall()

                # Формуємо відповідь
                response = f"🧑‍💼 <b>КЛІЄНТ #{client_info[0]}</b>\n"
                response += f"📛 <b>Ім'я:</b> {full_name}\n"
                response += f"📞 <b>Телефон:</b> {client_info[4] or 'Не вказано'}\n"
                response += f"💰 <b>Баланс бонусів:</b> {self.format_client_balance(client_info[5])} грн\n\n"

                # Статистика
                if bonus_stats:
                    response += "📊 <b>СТАТИСТИКА БОНУСІВ</b>\n"
                    total_earned = 0
                    total_spent = 0

                    for stat in bonus_stats:
                        op_type = stat[0]
                        count = stat[1]
                        amount = stat[2] or 0
                        amount_grn = float(amount) / 100.0

                        if op_type == "EARN":
                            total_earned += amount_grn
                            response += f"💚 Нараховано: {count} операцій, +{amount_grn:.2f} грн\n"
                        elif op_type == "SPEND":
                            total_spent += abs(amount_grn)
                            response += f"💸 Витрачено: {count} операцій, {amount_grn:.2f} грн\n"

                    response += (
                        f"\n📈 <b>Всього нараховано:</b> +{total_earned:.2f} грн\n"
                    )
                    response += f"📉 <b>Всього витрачено:</b> -{total_spent:.2f} грн\n"
                    response += f"🧮 <b>Розрахунковий баланс:</b> {total_earned - total_spent:.2f} грн\n\n"

                # Останні операції
                if bonus_history:
                    response += (
                        f"📋 <b>ОСТАННІ ОПЕРАЦІЇ (топ {len(bonus_history)})</b>\n"
                    )
                    for op in bonus_history:
                        tx_id = op[0] or "N/A"
                        op_type = op[1]
                        amount = self.format_client_balance(op[2])
                        balance_before = self.format_client_balance(op[3])
                        balance_after = self.format_client_balance(op[4])
                        description = op[5] or "Без опису"
                        processed_at = self.format_datetime(op[6])

                        symbol = {
                            "EARN": "💚 +",
                            "SPEND": "💸 ",
                            "ADJUST": "🔄 ",
                            "EXPIRE": "⏰ ",
                        }.get(op_type, "❓ ")

                        response += (
                            f"{symbol}{amount} | {balance_before} → {balance_after}\n"
                        )
                        response += f"📅 {processed_at} | TX: {tx_id}\n"
                        response += f"📝 {description}\n\n"

                # Останні транзакції
                if transactions:
                    response += (
                        f"🛒 <b>ОСТАННІ ТРАНЗАКЦІЇ (топ {len(transactions)})</b>\n"
                    )
                    for tx in transactions:
                        tx_id = tx[0]
                        tx_sum = tx[1]
                        bonus_percent = tx[2] if tx[2] else 0
                        paid_bonus = tx[3] if tx[3] else 0
                        date_close = self.format_datetime(tx[4])
                        spot_name = tx[5] or "Невідомий заклад"
                        products_list = tx[6] or "Товари не знайдені"

                        # Розрахунок нарахованих бонусів
                        if tx_sum and bonus_percent:
                            earned_bonus = tx_sum * bonus_percent / 100
                        else:
                            earned_bonus = 0

                        response += f"🧾 <b>Транзакція #{tx_id}</b>\n"
                        response += f"🏪 {spot_name}\n"
                        response += f"💰 Сума: {tx_sum:.2f} грн | Бонус: {bonus_percent:.1f}% | Нараховано: +{earned_bonus:.2f} грн\n"
                        response += f"💸 Оплачено бонусами: -{paid_bonus:.2f} грн\n"
                        response += f"📅 {date_close}\n"

                        # Товари (обмежуємо довжину)
                        if len(products_list) > 100:
                            products_list = products_list[:100] + "..."
                        response += f"🛍️ {products_list}\n\n"

                return response

        except Exception as e:
            self.logger.error(f"Помилка отримання історії {user_id}: {e}")
            return f"❌ Помилка отримання історії клієнта #{user_id}"

    async def add_bonus(
        self, user_id: int, amount: int, reason: str, admin_id: int
    ) -> bool:
        """Додати бонуси клієнту (в копійках)"""
        try:
            with self.engine.connect() as conn:
                # Спочатку шукаємо за client_id
                current_balance = conn.execute(
                    text(
                        "SELECT COALESCE(bonus, 0) FROM clients WHERE client_id = :client_id"
                    ),
                    {"client_id": user_id},
                ).scalar()

                # Якщо не знайшли за client_id, шукаємо за telegram_user_id
                client_id = user_id
                if current_balance is None:
                    result = conn.execute(
                        text(
                            "SELECT client_id, COALESCE(bonus, 0) FROM clients WHERE telegram_user_id = :telegram_user_id"
                        ),
                        {"telegram_user_id": user_id},
                    ).fetchone()
                    
                    if result:
                        client_id = result[0]  # може бути NULL для Telegram користувачів
                        current_balance = result[1]
                    else:
                        return False

                new_balance = current_balance + amount

                # Записуємо операцію в transaction_bonus
                # Для Telegram користувачів client_id може бути NULL, тому використовуємо telegram_user_id
                if client_id is not None:
                    # Poster клієнт - використовуємо client_id
                    conn.execute(
                        text(
                            """
                            INSERT INTO transaction_bonus (
                                client_id, operation_type, amount,
                                balance_before, balance_after, description,
                                processed_at, created_at, updated_at
                            ) VALUES (
                                :client_id, 'ADJUST', :amount,
                                :balance_before, :balance_after, :description,
                                NOW(), NOW(), NOW()
                            )
                        """
                        ),
                        {
                            "client_id": client_id,
                            "amount": amount,
                            "balance_before": current_balance,
                            "balance_after": new_balance,
                            "description": f"Корекція через Telegram бота: {reason} (Адмін: {admin_id})",
                        },
                    )
                    
                    # Оновлюємо баланс клієнта
                    conn.execute(
                        text(
                            """
                            UPDATE clients
                            SET bonus = :new_balance, updated_at = NOW()
                            WHERE client_id = :client_id
                        """
                        ),
                        {"client_id": client_id, "new_balance": new_balance},
                    )
                else:
                    # Telegram користувач без client_id - оновлюємо по telegram_user_id
                    conn.execute(
                        text(
                            """
                            UPDATE clients
                            SET bonus = :new_balance, updated_at = NOW()
                            WHERE telegram_user_id = :telegram_user_id
                        """
                        ),
                        {"telegram_user_id": user_id, "new_balance": new_balance},
                    )
                    # Не можемо записати в transaction_bonus без client_id
                    self.logger.warning(f"Оновлено баланс Telegram користувача {user_id} без запису в transaction_bonus")

                conn.commit()
                self.logger.info(
                    f"Додано {amount} копійок користувачу {user_id} (client_id: {client_id}) адміном {admin_id}"
                )
                return True

        except Exception as e:
            self.logger.error(f"Помилка додавання бонусів {user_id}: {e}")
            return False

    async def remove_bonus(
        self, user_id: int, amount: int, reason: str, admin_id: int
    ) -> bool:
        """Видалити бонуси у клієнта (в копійках)"""
        return await self.add_bonus(user_id, -amount, reason, admin_id)

    async def get_bonus_history(self, limit: int = 10) -> List[Dict]:
        """Отримати загальну історію бонусних операцій"""
        try:
            with self.engine.connect() as conn:
                results = conn.execute(
                    text(
                        """
                        SELECT
                            tb.id,
                            tb.client_id,
                            c.name,
                            c.phone,
                            tb.operation_type,
                            tb.amount,
                            tb.description,
                            tb.processed_at
                        FROM transaction_bonus tb
                        LEFT JOIN clients c ON tb.client_id = c.client_id
                        ORDER BY tb.processed_at DESC
                        LIMIT :limit
                    """
                    ),
                    {"limit": limit},
                ).fetchall()

                history = []
                for result in results:
                    history.append(
                        {
                            "id": result[0],
                            "client_id": result[1],
                            "client_name": result[2],
                            "client_phone": result[3],
                            "operation_type": result[4],
                            "amount": result[5],
                            "description": result[6],
                            "processed_at": result[7],
                        }
                    )

                return history
        except Exception as e:
            self.logger.error(f"Помилка отримання історії бонусів: {e}")
            return []

    async def admin_users(self, limit: int = 10) -> List[Dict]:
        """Отримати список користувачів для адміна"""
        try:
            with self.engine.connect() as conn:
                results = conn.execute(
                    text("""
                        SELECT client_id, firstname, lastname, phone, bonus, created_at, telegram_user_id
                        FROM clients 
                        WHERE telegram_user_id IS NOT NULL 
                        ORDER BY created_at DESC 
                        LIMIT :limit
                    """),
                    {"limit": limit}
                ).fetchall()

                users = []
                for result in results:
                    name_parts = []
                    if result[1]:  # firstname
                        name_parts.append(result[1])
                    if result[2]:  # lastname  
                        name_parts.append(result[2])
                    
                    full_name = " ".join(name_parts) if name_parts else "Не вказано"
                    
                    users.append({
                        "client_id": result[0],
                        "name": full_name,
                        "phone": result[3],
                        "bonus": result[4],
                        "created_at": result[5],
                        "telegram_user_id": result[6]
                    })
                return users
        except Exception as e:
            self.logger.error(f"Помилка отримання списку користувачів: {e}")
            return []

    async def admin_users(self, limit: int = 10) -> List[Dict]:
        """Отримати список користувачів для адмін-панелі"""
        try:
            with self.engine.connect() as conn:
                results = conn.execute(
                    text("""
                        SELECT client_id, firstname, lastname, patronymic, phone, bonus, 
                               created_at, telegram_user_id, telegram_username, 
                               telegram_first_name, telegram_last_name
                        FROM clients 
                        WHERE telegram_user_id IS NOT NULL
                        ORDER BY telegram_last_activity DESC NULLS LAST, created_at DESC
                        LIMIT :limit
                    """),
                    {"limit": limit}
                ).fetchall()
                
                users = []
                for result in results:
                    name_parts = []
                    if result[1]:  # firstname
                        name_parts.append(result[1])
                    if result[2]:  # lastname  
                        name_parts.append(result[2])
                    if result[3]:  # patronymic
                        name_parts.append(result[3])
                    
                    full_name = " ".join(name_parts) if name_parts else "Не вказано"
                    
                    users.append({
                        "client_id": result[0],
                        "name": full_name,
                        "phone": result[4],
                        "bonus": result[5],
                        "created_at": result[6],
                        "telegram_user_id": result[7],
                        "telegram_username": result[8],
                        "telegram_first_name": result[9],
                        "telegram_last_name": result[10]
                    })
                return users
        except Exception as e:
            self.logger.error(f"Помилка отримання користувачів для адміна: {e}")
            return []

    def table_exists(self, table_name: str) -> bool:
        """Перевірити чи існує таблиця"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = :table_name
                        )
                    """),
                    {"table_name": table_name}
                ).scalar()
                return bool(result)
        except Exception as e:
            self.logger.error(f"Помилка перевірки існування таблиці {table_name}: {e}")
            return False

    async def upsert_user(self, user_id: int, username: str = None, **kwargs):
        """Створити або оновити користувача в таблиці clients"""
        try:
            with self.engine.connect() as conn:
                # Спочатку перевіряємо, чи існує користувач з таким telegram_user_id
                existing_user = conn.execute(
                    text(
                        "SELECT client_id FROM clients WHERE telegram_user_id = :telegram_user_id"
                    ),
                    {"telegram_user_id": user_id},
                ).fetchone()

                if existing_user:
                    # Оновлюємо існуючого користувача
                    conn.execute(
                        text(
                            """
                            UPDATE clients
                            SET telegram_username = :telegram_username,
                                telegram_first_name = :telegram_first_name,
                                telegram_last_name = :telegram_last_name,
                                telegram_language_code = :telegram_language_code,
                                is_telegram_active = true,
                                telegram_last_activity = NOW(),
                                updated_at = NOW()
                            WHERE telegram_user_id = :telegram_user_id
                        """
                        ),
                        {
                            "telegram_user_id": user_id,
                            "telegram_username": username,
                            "telegram_first_name": kwargs.get("first_name"),
                            "telegram_last_name": kwargs.get("last_name"),
                            "telegram_language_code": kwargs.get("language_code", "uk"),
                        },
                    )
                    self.logger.info(
                        f"Оновлено Telegram дані для існуючого клієнта {existing_user[0]}"
                    )
                else:
                    # Створюємо нового клієнта з client_id в діапазоні 900000000+ (щоб не конфліктувати з Poster)
                    import uuid

                    # Генеруємо client_id на основі telegram_user_id в діапазоні 900000000+
                    telegram_client_id = 900000000 + user_id

                    conn.execute(
                        text(
                            """
                            INSERT INTO clients (
                                id, client_id, firstname, lastname,
                                telegram_user_id, telegram_username, telegram_first_name, telegram_last_name,
                                telegram_language_code, is_telegram_active, telegram_joined_at, telegram_last_activity,
                                bonus, created_at, updated_at, is_active
                            ) VALUES (
                                :id, :client_id, :firstname, :lastname,
                                :telegram_user_id, :telegram_username, :telegram_first_name, :telegram_last_name,
                                :telegram_language_code, true, NOW(), NOW(),
                                0, NOW(), NOW(), true
                            )
                        """
                        ),
                        {
                            "id": str(uuid.uuid4()),
                            "client_id": telegram_client_id,
                            "firstname": kwargs.get("first_name", "Telegram"),
                            "lastname": kwargs.get("last_name", "User"),
                            "telegram_user_id": user_id,
                            "telegram_username": username,
                            "telegram_first_name": kwargs.get("first_name"),
                            "telegram_last_name": kwargs.get("last_name"),
                            "telegram_language_code": kwargs.get("language_code", "uk"),
                        },
                    )
                    self.logger.info(
                        f"Створено нового Telegram користувача з client_id {telegram_client_id} для telegram_user_id {user_id}"
                    )

                conn.commit()
                return True

        except Exception as e:
            self.logger.error(f"Помилка upsert користувача {user_id}: {e}")
            return False


# Глобальний екземпляр сервісу
_postgresql_bonus_service = None


def get_postgresql_bonus_service(database_url: str = None) -> PostgreSQLBonusService:
    """Отримати екземпляр PostgreSQL бонусного сервісу"""
    global _postgresql_bonus_service

    if _postgresql_bonus_service is None and database_url:
        _postgresql_bonus_service = PostgreSQLBonusService(database_url)

    return _postgresql_bonus_service

-- PostgreSQL тригери та функції для автоматичного розрахунку бонусів
-- Файл: bonus_triggers.sql

-- =====================================================
-- 1. Створення таблиці системних налаштувань
-- =====================================================
CREATE TABLE IF NOT EXISTS system_settings (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Індекс для швидшого пошуку
CREATE INDEX IF NOT EXISTS idx_system_settings_key ON system_settings(key);

-- Тригер для оновлення updated_at в system_settings
CREATE OR REPLACE FUNCTION update_system_settings_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_system_settings_updated_at ON system_settings;
CREATE TRIGGER trigger_system_settings_updated_at
    BEFORE UPDATE ON system_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_system_settings_updated_at();

-- =====================================================
-- 2. Створення таблиці transaction_bonus
-- =====================================================
CREATE TABLE IF NOT EXISTS transaction_bonus (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Links
    client_id BIGINT NOT NULL REFERENCES clients(client_id),
    transaction_id BIGINT REFERENCES transactions(transaction_id),

    -- Operation details
    operation_type VARCHAR(20) NOT NULL CHECK (operation_type IN ('EARN', 'SPEND', 'ADJUST', 'EXPIRE')),

    -- Amounts
    amount NUMERIC(10,2) NOT NULL,
    balance_before NUMERIC(10,2) NOT NULL,
    balance_after NUMERIC(10,2) NOT NULL,

    -- Details
    description TEXT,
    bonus_percent NUMERIC(5,2),
    transaction_sum NUMERIC(10,2),

    -- System
    processed_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Створення індексів для transaction_bonus
CREATE INDEX IF NOT EXISTS ix_transaction_bonus_client_id ON transaction_bonus(client_id);
CREATE INDEX IF NOT EXISTS ix_transaction_bonus_transaction_id ON transaction_bonus(transaction_id);
CREATE INDEX IF NOT EXISTS ix_transaction_bonus_operation_type ON transaction_bonus(operation_type);
CREATE INDEX IF NOT EXISTS ix_transaction_bonus_created_at ON transaction_bonus(created_at);
CREATE INDEX IF NOT EXISTS ix_transaction_bonus_processed_at ON transaction_bonus(processed_at);

-- =====================================================
-- 3. Функції для роботи з налаштуваннями
-- =====================================================

-- Функція для отримання налаштування
CREATE OR REPLACE FUNCTION get_setting(setting_key VARCHAR)
RETURNS TEXT AS $$
DECLARE
    result TEXT;
BEGIN
    SELECT value INTO result
    FROM system_settings
    WHERE key = setting_key;

    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Функція для встановлення налаштування
CREATE OR REPLACE FUNCTION set_setting(setting_key VARCHAR, setting_value TEXT, setting_description TEXT DEFAULT NULL)
RETURNS VOID AS $$
BEGIN
    INSERT INTO system_settings (key, value, description)
    VALUES (setting_key, setting_value, setting_description)
    ON CONFLICT (key) DO UPDATE SET
        value = EXCLUDED.value,
        description = COALESCE(EXCLUDED.description, system_settings.description),
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 4. Головна функція тригера для обробки бонусів
-- =====================================================
CREATE OR REPLACE FUNCTION process_bonus_operations()
RETURNS TRIGGER AS $$
DECLARE
    client_current_bonus_kopecks NUMERIC(10,2) := 0; -- Баланс в копійках з clients.bonus
    client_current_bonus_grn NUMERIC(10,2) := 0;     -- Баланс в гривнях для операцій
    earned_bonus NUMERIC(10,2) := 0;                 -- В гривнях для розрахунків
    spent_bonus NUMERIC(10,2) := 0;                  -- В гривнях для розрахунків
    earned_bonus_kopecks NUMERIC(10,2) := 0;         -- В копійках для збереження в amount
    spent_bonus_kopecks NUMERIC(10,2) := 0;          -- В копійках для збереження в amount
    bonus_start_date DATE;
    bonus_system_enabled BOOLEAN := false;
BEGIN
    -- Отримуємо налаштування бонусної системи
    SELECT
        COALESCE((SELECT value::DATE FROM system_settings WHERE key = 'bonus_system_start_date'), '2025-09-01'),
        COALESCE((SELECT value::BOOLEAN FROM system_settings WHERE key = 'bonus_system_enabled'), false)
    INTO bonus_start_date, bonus_system_enabled;

    -- Перевіряємо, чи увімкнена бонусна система
    IF NOT bonus_system_enabled THEN
        RETURN NEW;
    END IF;

    -- Обробляємо тільки закриті транзакції з клієнтом після встановленої дати
    IF NEW.client_id IS NOT NULL
       AND NEW.date_close IS NOT NULL
       AND NEW.date_close::DATE >= bonus_start_date THEN

        -- Отримуємо поточний баланс бонусів клієнта в копійках
        SELECT COALESCE(bonus, 0) INTO client_current_bonus_kopecks
        FROM clients
        WHERE client_id = NEW.client_id;

        -- Додаткова перевірка на NULL
        client_current_bonus_kopecks := COALESCE(client_current_bonus_kopecks, 0);

        -- Конвертуємо копійки в гривні для розрахунків
        client_current_bonus_grn := client_current_bonus_kopecks / 100.0;

        -- Якщо це INSERT (нова транзакція)
        IF TG_OP = 'INSERT' THEN

            -- Перевіряємо чи вже є бонусні операції для цієї транзакції
            IF EXISTS (SELECT 1 FROM transaction_bonus WHERE transaction_id = NEW.transaction_id) THEN
                RETURN NEW;
            END IF;

            -- Рахуємо нараховані бонуси (в гривнях)
            earned_bonus := CASE
                WHEN NEW.bonus > 0 THEN ROUND((NEW.sum * NEW.bonus / 100), 2)
                ELSE 0
            END;

            -- Отримуємо витрачені бонуси (в гривнях)
            spent_bonus := COALESCE(NEW.payed_bonus, 0);

            -- Конвертуємо в копійки для збереження в amount
            earned_bonus_kopecks := ROUND(earned_bonus * 100, 0);
            spent_bonus_kopecks := ROUND(spent_bonus * 100, 0);

            -- Записуємо списання бонусів (якщо є)
            IF spent_bonus > 0 THEN
                INSERT INTO transaction_bonus (
                    client_id, transaction_id, operation_type, amount,
                    balance_before, balance_after, description,
                    processed_at, created_at, updated_at
                ) VALUES (
                    NEW.client_id, NEW.transaction_id, 'SPEND', -spent_bonus_kopecks,  -- В копійках!
                    client_current_bonus_kopecks, client_current_bonus_kopecks - spent_bonus_kopecks,
                    'Оплата бонусами за транзакцію #' || NEW.transaction_id,  -- Українською!
                    COALESCE(NEW.date_close, NOW()), NOW(), NOW()
                );

                client_current_bonus_grn := client_current_bonus_grn - spent_bonus;
                client_current_bonus_kopecks := client_current_bonus_kopecks - spent_bonus_kopecks;
            END IF;

            -- Записуємо нарахування бонусів (якщо є)
            IF earned_bonus > 0 THEN
                INSERT INTO transaction_bonus (
                    client_id, transaction_id, operation_type, amount,
                    balance_before, balance_after, description,
                    bonus_percent, transaction_sum, processed_at,
                    created_at, updated_at
                ) VALUES (
                    NEW.client_id, NEW.transaction_id, 'EARN', earned_bonus_kopecks,  -- В копійках!
                    client_current_bonus_kopecks, client_current_bonus_kopecks + earned_bonus_kopecks,
                    'Нарахування ' || NEW.bonus || '% бонусів за транзакцію #' || NEW.transaction_id,  -- Українською!
                    NEW.bonus, NEW.sum, COALESCE(NEW.date_close, NOW()),
                    NOW(), NOW()
                );

                client_current_bonus_grn := client_current_bonus_grn + earned_bonus;
                client_current_bonus_kopecks := client_current_bonus_kopecks + earned_bonus_kopecks;
            END IF;

            -- Оновлюємо баланс клієнта (в копійках)
            IF spent_bonus > 0 OR earned_bonus > 0 THEN
                UPDATE clients
                SET bonus = client_current_bonus_kopecks,  -- Зберігаємо в копійках
                    updated_at = NOW()
                WHERE client_id = NEW.client_id;

                -- Логуємо операцію
                RAISE NOTICE 'Бонусна операція для клієнта % (транзакція %): нараховано=% копійок, витрачено=% копійок, новий баланс=%',
                    NEW.client_id, NEW.transaction_id, earned_bonus_kopecks, spent_bonus_kopecks, client_current_bonus_kopecks;
            END IF;

        END IF;

    END IF;

    RETURN NEW;

EXCEPTION
    WHEN OTHERS THEN
        -- Логуємо помилку, але не перериваємо транзакцію
        RAISE NOTICE 'Помилка в тригері process_bonus_operations для транзакції %: %',
            COALESCE(NEW.transaction_id, OLD.transaction_id), SQLERRM;
        RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 5. Тригер для transactions (INSERT/UPDATE)
-- =====================================================
DROP TRIGGER IF EXISTS trigger_process_bonus_operations ON transactions;

CREATE TRIGGER trigger_process_bonus_operations
    AFTER INSERT OR UPDATE ON transactions
    FOR EACH ROW
    EXECUTE FUNCTION process_bonus_operations();

-- =====================================================
-- 6. Функція для управління бонусними тригерами
-- =====================================================
CREATE OR REPLACE FUNCTION manage_bonus_triggers(enable_triggers BOOLEAN)
RETURNS TEXT AS $$
DECLARE
    result_message TEXT;
BEGIN
    IF enable_triggers THEN
        -- Увімкнути тригер
        ALTER TABLE transactions ENABLE TRIGGER trigger_process_bonus_operations;

        -- Увімкнути бонусну систему в налаштуваннях
        PERFORM set_setting('bonus_system_enabled', 'true');

        result_message := 'Bonus triggers ENABLED successfully';
    ELSE
        -- Вимкнути тригер
        ALTER TABLE transactions DISABLE TRIGGER trigger_process_bonus_operations;

        -- Вимкнути бонусну систему в налаштуваннях
        PERFORM set_setting('bonus_system_enabled', 'false');

        result_message := 'Bonus triggers DISABLED successfully';
    END IF;

    RETURN result_message;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 7. Функція для пересчету всіх бонусів
-- =====================================================
CREATE OR REPLACE FUNCTION recalculate_all_bonuses_with_trigger()
RETURNS TABLE(
    total_transactions BIGINT,
    updated_transactions BIGINT,
    total_earned NUMERIC(10,2),
    total_spent NUMERIC(10,2)
) AS $$
DECLARE
    bonus_start_date DATE;
    total_count BIGINT := 0;
    updated_count BIGINT := 0;
    earned_sum NUMERIC(10,2) := 0;
    spent_sum NUMERIC(10,2) := 0;
    rec RECORD;
BEGIN
    -- Отримуємо дату початку бонусної системи
    SELECT COALESCE(value::DATE, '2025-09-01') INTO bonus_start_date
    FROM system_settings
    WHERE key = 'bonus_system_start_date';

    -- Видаляємо всі старі бонусні операції
    DELETE FROM transaction_bonus;
    RAISE NOTICE 'Deleted all existing bonus operations';

    -- Обнуляємо бонуси клієнтів
    UPDATE clients SET bonus = 0;
    RAISE NOTICE 'Reset all client bonuses to 0';

    -- Отримуємо загальну кількість транзакцій для обробки
    SELECT COUNT(*) INTO total_count
    FROM transactions t
    WHERE t.client_id IS NOT NULL
        AND t.date_close IS NOT NULL
        AND t.date_close::DATE >= bonus_start_date;

    RAISE NOTICE 'Found % transactions to process', total_count;

    -- Тимчасово вимикаємо тригер щоб уникнути подвійної обробки під час UPDATE
    ALTER TABLE transactions DISABLE TRIGGER trigger_process_bonus_operations;

    -- Обробляємо кожну підходящу транзакцію вручну
    FOR rec IN
        SELECT transaction_id, client_id, sum, bonus, payed_bonus, date_close
        FROM transactions t
        WHERE t.client_id IS NOT NULL
            AND t.date_close IS NOT NULL
            AND t.date_close::DATE >= bonus_start_date
        ORDER BY t.date_close ASC
    LOOP
        -- Викликаємо логіку тригера вручну
        PERFORM process_bonus_operations_manual(rec.transaction_id, rec.client_id, rec.sum, rec.bonus, rec.payed_bonus, rec.date_close);
        updated_count := updated_count + 1;

        -- Логуємо прогрес кожні 1000 транзакцій
        IF updated_count % 1000 = 0 THEN
            RAISE NOTICE 'Processed % of % transactions', updated_count, total_count;
        END IF;
    END LOOP;

    -- Включаємо тригер назад
    ALTER TABLE transactions ENABLE TRIGGER trigger_process_bonus_operations;

    -- Рахуємо загальні суми
    SELECT
        COALESCE(SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END), 0),
        COALESCE(SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END), 0)
    INTO earned_sum, spent_sum
    FROM transaction_bonus;

    RAISE NOTICE 'Bonus recalculation completed: % transactions processed, earned: %, spent: %',
        updated_count, earned_sum, spent_sum;

    RETURN QUERY SELECT total_count, updated_count, earned_sum, spent_sum;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 8. Допоміжна функція для ручної обробки транзакції
-- =====================================================
CREATE OR REPLACE FUNCTION process_bonus_operations_manual(
    p_transaction_id BIGINT,
    p_client_id BIGINT,
    p_sum NUMERIC(10,2),
    p_bonus NUMERIC(5,2),
    p_payed_bonus NUMERIC(10,2),
    p_date_close TIMESTAMP
)
RETURNS VOID AS $$
DECLARE
    client_current_bonus_kopecks NUMERIC(10,2) := 0; -- Баланс в копійках з clients.bonus
    client_current_bonus_grn NUMERIC(10,2) := 0;     -- Баланс в гривнях для операцій
    earned_bonus NUMERIC(10,2) := 0;                 -- В гривнях для розрахунків
    spent_bonus NUMERIC(10,2) := 0;                  -- В гривнях для розрахунків
    earned_bonus_kopecks NUMERIC(10,2) := 0;         -- В копійках для збереження в amount
    spent_bonus_kopecks NUMERIC(10,2) := 0;          -- В копійках для збереження в amount
BEGIN
    -- Отримуємо поточний баланс бонусів клієнта в копійках
    SELECT COALESCE(bonus, 0) INTO client_current_bonus_kopecks
    FROM clients
    WHERE client_id = p_client_id;

    -- Додаткова перевірка на NULL
    client_current_bonus_kopecks := COALESCE(client_current_bonus_kopecks, 0);

    -- Конвертуємо копійки в гривні для розрахунків
    client_current_bonus_grn := client_current_bonus_kopecks / 100.0;

    -- Рахуємо нараховані бонуси (в гривнях)
    earned_bonus := CASE
        WHEN p_bonus > 0 THEN ROUND((p_sum * p_bonus / 100), 2)
        ELSE 0
    END;

    -- Отримуємо витрачені бонуси (в гривнях)
    spent_bonus := COALESCE(p_payed_bonus, 0);

    -- Конвертуємо в копійки для збереження в amount
    earned_bonus_kopecks := ROUND(earned_bonus * 100, 0);
    spent_bonus_kopecks := ROUND(spent_bonus * 100, 0);

    -- Записуємо списання бонусів (якщо є)
    IF spent_bonus > 0 THEN
        INSERT INTO transaction_bonus (
            client_id, transaction_id, operation_type, amount,
            balance_before, balance_after, description,
            processed_at, created_at, updated_at
        ) VALUES (
            p_client_id, p_transaction_id, 'SPEND', -spent_bonus_kopecks,  -- В копійках!
            client_current_bonus_kopecks, client_current_bonus_kopecks - spent_bonus_kopecks,
            'Оплата бонусами за транзакцію #' || p_transaction_id,  -- Українською!
            p_date_close, NOW(), NOW()
        );

        client_current_bonus_grn := client_current_bonus_grn - spent_bonus;
        client_current_bonus_kopecks := client_current_bonus_kopecks - spent_bonus_kopecks;
    END IF;

    -- Записуємо нарахування бонусів (якщо є)
    IF earned_bonus > 0 THEN
        INSERT INTO transaction_bonus (
            client_id, transaction_id, operation_type, amount,
            balance_before, balance_after, description,
            bonus_percent, transaction_sum, processed_at,
            created_at, updated_at
        ) VALUES (
            p_client_id, p_transaction_id, 'EARN', earned_bonus_kopecks,  -- В копійках!
            client_current_bonus_kopecks, client_current_bonus_kopecks + earned_bonus_kopecks,
            'Нарахування ' || p_bonus || '% бонусів за транзакцію #' || p_transaction_id,  -- Українською!
            p_bonus, p_sum, p_date_close,
            NOW(), NOW()
        );

        client_current_bonus_grn := client_current_bonus_grn + earned_bonus;
        client_current_bonus_kopecks := client_current_bonus_kopecks + earned_bonus_kopecks;
    END IF;

    -- Оновлюємо баланс клієнта (в копійках)
    IF spent_bonus > 0 OR earned_bonus > 0 THEN
        UPDATE clients
        SET bonus = client_current_bonus_kopecks,  -- Зберігаємо в копійках
            updated_at = NOW()
        WHERE client_id = p_client_id;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 9. Встановлення початкових налаштувань
-- =====================================================

-- Вставляємо початкові налаштування
INSERT INTO system_settings (key, value, description) VALUES
('bonus_system_start_date', '2025-09-01', 'Дата початку роботи бонусної системи'),
('bonus_system_enabled', 'true', 'Чи увімкнена бонусна система'),
('default_bonus_percent', '5.0', 'Процент бонусів за замовчуванням')
ON CONFLICT (key) DO UPDATE SET
    value = EXCLUDED.value,
    description = EXCLUDED.description,
    updated_at = NOW();

-- =====================================================
-- 10. Повідомлення про успішне встановлення
-- =====================================================
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=================================================';
    RAISE NOTICE '✅ Bonus system successfully installed!';
    RAISE NOTICE '=================================================';
    RAISE NOTICE '📋 Created tables:';
    RAISE NOTICE '   - system_settings';
    RAISE NOTICE '   - transaction_bonus';
    RAISE NOTICE '';
    RAISE NOTICE '🔧 Created functions:';
    RAISE NOTICE '   - get_setting()';
    RAISE NOTICE '   - set_setting()';
    RAISE NOTICE '   - process_bonus_operations()';
    RAISE NOTICE '   - manage_bonus_triggers()';
    RAISE NOTICE '   - recalculate_all_bonuses_with_trigger()';
    RAISE NOTICE '';
    RAISE NOTICE '⚡ Created triggers:';
    RAISE NOTICE '   - trigger_process_bonus_operations (ENABLED)';
    RAISE NOTICE '';
    RAISE NOTICE '⚙️  Initial settings:';
    RAISE NOTICE '   - bonus_system_enabled: true';
    RAISE NOTICE '   - bonus_system_start_date: 2025-09-01';
    RAISE NOTICE '   - default_bonus_percent: 5.0';
    RAISE NOTICE '';
    RAISE NOTICE '🚀 Ready to use! Run transactions to see bonus operations.';
    RAISE NOTICE '=================================================';
END $$;

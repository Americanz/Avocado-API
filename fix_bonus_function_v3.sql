-- Виправлення функцій для правильного зберігання amount в копійках
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
            'Оплата бонусами за транзакцію #' || p_transaction_id,
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
            'Нарахування ' || p_bonus || '% бонусів за транзакцію #' || p_transaction_id,
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

-- Також виправляємо основну функцію тригера process_bonus_operations
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
                    'Оплата бонусами за транзакцію #' || NEW.transaction_id,
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
                    'Нарахування ' || NEW.bonus || '% бонусів за транзакцію #' || NEW.transaction_id,
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
                RAISE NOTICE 'Bonus operation for client % (transaction %): earned=% kopecks, spent=% kopecks, new_balance=%',
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

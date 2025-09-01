-- Виправлення функції process_bonus_operations_manual
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
    client_current_bonus NUMERIC(10,2) := 0;
    earned_bonus NUMERIC(10,2) := 0;
    spent_bonus NUMERIC(10,2) := 0;
BEGIN
    -- Отримуємо поточний баланс бонусів клієнта (ОБОВ'ЯЗКОВО з COALESCE)
    SELECT COALESCE(bonus, 0) INTO client_current_bonus
    FROM clients
    WHERE client_id = p_client_id;

    -- Додаткова перевірка на NULL
    client_current_bonus := COALESCE(client_current_bonus, 0);

    -- Рахуємо нараховані бонуси
    earned_bonus := CASE
        WHEN p_bonus > 0 THEN ROUND((p_sum * p_bonus / 100), 2)
        ELSE 0
    END;

    -- Отримуємо витрачені бонуси
    spent_bonus := COALESCE(p_payed_bonus, 0);

    -- Записуємо списання бонусів (якщо є)
    IF spent_bonus > 0 THEN
        INSERT INTO transaction_bonus (
            client_id, transaction_id, operation_type, amount,
            balance_before, balance_after, description,
            processed_at, created_at, updated_at
        ) VALUES (
            p_client_id, p_transaction_id, 'SPEND', -spent_bonus,
            client_current_bonus, client_current_bonus - spent_bonus,
            'Оплата бонусами за транзакцію #' || p_transaction_id,
            p_date_close, NOW(), NOW()
        );

        client_current_bonus := client_current_bonus - spent_bonus;
    END IF;

    -- Записуємо нарахування бонусів (якщо є)
    IF earned_bonus > 0 THEN
        INSERT INTO transaction_bonus (
            client_id, transaction_id, operation_type, amount,
            balance_before, balance_after, description,
            bonus_percent, transaction_sum, processed_at,
            created_at, updated_at
        ) VALUES (
            p_client_id, p_transaction_id, 'EARN', earned_bonus,
            client_current_bonus, client_current_bonus + earned_bonus,
            'Нарахування ' || p_bonus || '% бонусів за транзакцію #' || p_transaction_id,
            p_bonus, p_sum, p_date_close,
            NOW(), NOW()
        );

        client_current_bonus := client_current_bonus + earned_bonus;
    END IF;

    -- Оновлюємо баланс клієнта тільки якщо були зміни
    IF spent_bonus > 0 OR earned_bonus > 0 THEN
        UPDATE clients
        SET bonus = client_current_bonus,
            updated_at = NOW()
        WHERE client_id = p_client_id;
    END IF;
END;
$$ LANGUAGE plpgsql;

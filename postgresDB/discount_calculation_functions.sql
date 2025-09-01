-- PostgreSQL функції для розрахунку знижок
-- Файл: discount_calculation_functions.sql

-- =====================================================
-- 1. Функція для батчового розрахунку real discount
-- =====================================================
CREATE OR REPLACE FUNCTION calculate_batch_real_discounts(
    transaction_ids BIGINT[]
)
RETURNS TABLE (
    transaction_id BIGINT,
    real_discount NUMERIC(10,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        tp.transaction_id,
        COALESCE(
            GREATEST(
                SUM(tp.sum) - COALESCE(t.payed_sum, 0) - COALESCE(t.payed_bonus, 0),
                0
            ),
            0
        )::NUMERIC(10,2) as real_discount
    FROM transaction_products tp
    JOIN transactions t ON tp.transaction_id = t.transaction_id
    WHERE tp.transaction_id = ANY(transaction_ids)
    GROUP BY tp.transaction_id, t.payed_sum, t.payed_bonus;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 2. Функція для оновлення discount в транзакціях
-- =====================================================
CREATE OR REPLACE FUNCTION update_transactions_discounts(
    transaction_ids BIGINT[]
)
RETURNS TABLE (
    transaction_id BIGINT,
    old_discount NUMERIC(10,2),
    new_discount NUMERIC(10,2),
    updated BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    WITH discount_calculations AS (
        SELECT
            tp.transaction_id,
            COALESCE(
                GREATEST(
                    SUM(tp.sum) - COALESCE(t.payed_sum, 0) - COALESCE(t.payed_bonus, 0),
                    0
                ),
                0
            )::NUMERIC(10,2) as calculated_discount
        FROM transaction_products tp
        JOIN transactions t ON tp.transaction_id = t.transaction_id
        WHERE tp.transaction_id = ANY(transaction_ids)
        GROUP BY tp.transaction_id, t.payed_sum, t.payed_bonus
    ),
    updates AS (
        UPDATE transactions t
        SET discount = dc.calculated_discount
        FROM discount_calculations dc
        WHERE t.transaction_id = dc.transaction_id
        RETURNING t.transaction_id, t.discount as new_discount
    )
    SELECT
        COALESCE(u.transaction_id, dc.transaction_id) as transaction_id,
        COALESCE(t_old.discount, 0)::NUMERIC(10,2) as old_discount,
        COALESCE(u.new_discount, dc.calculated_discount)::NUMERIC(10,2) as new_discount,
        (u.transaction_id IS NOT NULL) as updated
    FROM discount_calculations dc
    LEFT JOIN updates u ON dc.transaction_id = u.transaction_id
    LEFT JOIN transactions t_old ON dc.transaction_id = t_old.transaction_id;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 3. Функція для розрахунку одного discount (для тестування)
-- =====================================================
CREATE OR REPLACE FUNCTION calculate_single_real_discount(
    transaction_id_param BIGINT
)
RETURNS NUMERIC(10,2) AS $$
DECLARE
    result NUMERIC(10,2);
BEGIN
    SELECT
        COALESCE(
            GREATEST(
                SUM(tp.sum) - COALESCE(t.payed_sum, 0) - COALESCE(t.payed_bonus, 0),
                0
            ),
            0
        )::NUMERIC(10,2)
    INTO result
    FROM transaction_products tp
    JOIN transactions t ON tp.transaction_id = t.transaction_id
    WHERE tp.transaction_id = transaction_id_param;

    RETURN COALESCE(result, 0);
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 4. Функція для масового перерахунку всіх discount
-- =====================================================
CREATE OR REPLACE FUNCTION recalculate_all_discounts()
RETURNS TABLE (
    total_transactions BIGINT,
    updated_count BIGINT,
    total_discount NUMERIC(10,2)
) AS $$
DECLARE
    processed_count BIGINT;
    total_count BIGINT;
    sum_discount NUMERIC(10,2);
BEGIN
    -- Отримуємо загальну кількість транзакцій
    SELECT COUNT(*) INTO total_count FROM transactions;

    -- Оновлюємо всі discount за допомогою JOIN з підзапитом
    WITH discount_calculations AS (
        SELECT
            tp.transaction_id,
            COALESCE(
                GREATEST(
                    SUM(tp.sum) - COALESCE(t.payed_sum, 0) - COALESCE(t.payed_bonus, 0),
                    0
                ),
                0
            )::NUMERIC(10,2) as calculated_discount
        FROM transaction_products tp
        JOIN transactions t ON tp.transaction_id = t.transaction_id
        GROUP BY tp.transaction_id, t.payed_sum, t.payed_bonus
    )
    UPDATE transactions t
    SET discount = dc.calculated_discount
    FROM discount_calculations dc
    WHERE t.transaction_id = dc.transaction_id;

    GET DIAGNOSTICS processed_count = ROW_COUNT;

    -- Підраховуємо загальну суму знижок
    SELECT SUM(discount) INTO sum_discount FROM transactions WHERE discount > 0;

    RETURN QUERY
    SELECT
        total_count,
        processed_count,
        COALESCE(sum_discount, 0)::NUMERIC(10,2);
END;
$$ LANGUAGE plpgsql;

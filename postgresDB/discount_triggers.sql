-- PostgreSQL тригери для автоматичного розрахунку discount
-- Файл: discount_triggers.sql

-- =====================================================
-- 1. Функція тригера для розрахунку discount
-- =====================================================
CREATE OR REPLACE FUNCTION auto_calculate_transaction_discount()
RETURNS TRIGGER AS $$
DECLARE
    calculated_discount NUMERIC(10,2);
    target_transaction_id BIGINT;
BEGIN
    -- Визначаємо transaction_id залежно від операції
    IF TG_OP = 'DELETE' THEN
        target_transaction_id := OLD.transaction_id;
    ELSE
        target_transaction_id := NEW.transaction_id;
    END IF;
    
    -- Розраховуємо discount для цієї транзакції
    SELECT 
        COALESCE(
            GREATEST(
                products_sum - COALESCE(t.payed_sum, 0) - COALESCE(t.payed_bonus, 0),
                0
            ), 
            0
        )::NUMERIC(10,2)
    INTO calculated_discount
    FROM (
        SELECT 
            tp.transaction_id,
            SUM(tp.sum) as products_sum
        FROM transaction_products tp
        WHERE tp.transaction_id = target_transaction_id
        GROUP BY tp.transaction_id
    ) tp_sum
    JOIN transactions t ON tp_sum.transaction_id = t.transaction_id;
    
    -- Оновлюємо discount в таблиці transactions
    UPDATE transactions 
    SET discount = COALESCE(calculated_discount, 0)
    WHERE transaction_id = target_transaction_id;
    
    -- Логуємо зміни (опціонально)
    RAISE NOTICE 'Auto-calculated discount for transaction %: %', target_transaction_id, COALESCE(calculated_discount, 0);
    
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 2. Тригер для transaction_products (INSERT/UPDATE/DELETE)
-- =====================================================
DROP TRIGGER IF EXISTS trigger_auto_calculate_discount_on_products ON transaction_products;

CREATE TRIGGER trigger_auto_calculate_discount_on_products
    AFTER INSERT OR UPDATE OR DELETE ON transaction_products
    FOR EACH ROW
    EXECUTE FUNCTION auto_calculate_transaction_discount();

-- =====================================================
-- 3. Тригер для transactions (UPDATE payment fields)
-- =====================================================
DROP TRIGGER IF EXISTS trigger_auto_calculate_discount_on_payments ON transactions;

CREATE TRIGGER trigger_auto_calculate_discount_on_payments
    AFTER UPDATE OF payed_sum, payed_bonus ON transactions
    FOR EACH ROW
    WHEN (OLD.payed_sum IS DISTINCT FROM NEW.payed_sum 
          OR OLD.payed_bonus IS DISTINCT FROM NEW.payed_bonus)
    EXECUTE FUNCTION auto_calculate_transaction_discount();

-- =====================================================
-- 4. Функція для однократового перерахунку всіх discount
-- =====================================================
CREATE OR REPLACE FUNCTION recalculate_all_discounts_with_trigger()
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
    
    -- Тимчасово відключаємо тригер для масового оновлення
    ALTER TABLE transactions DISABLE TRIGGER trigger_auto_calculate_discount_on_payments;
    
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
    
    -- Включаємо тригер назад
    ALTER TABLE transactions ENABLE TRIGGER trigger_auto_calculate_discount_on_payments;
    
    -- Підраховуємо загальну суму знижок
    SELECT SUM(discount) INTO sum_discount FROM transactions WHERE discount > 0;
    
    RETURN QUERY
    SELECT 
        total_count,
        processed_count,
        COALESCE(sum_discount, 0)::NUMERIC(10,2);
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 5. Функція для керування тригерами (включення/відключення)
-- =====================================================
CREATE OR REPLACE FUNCTION manage_discount_triggers(enable_triggers BOOLEAN)
RETURNS TEXT AS $$
BEGIN
    IF enable_triggers THEN
        -- Включаємо тригери
        ALTER TABLE transaction_products ENABLE TRIGGER trigger_auto_calculate_discount_on_products;
        ALTER TABLE transactions ENABLE TRIGGER trigger_auto_calculate_discount_on_payments;
        RETURN 'Discount triggers ENABLED';
    ELSE
        -- Відключаємо тригери
        ALTER TABLE transaction_products DISABLE TRIGGER trigger_auto_calculate_discount_on_products;
        ALTER TABLE transactions DISABLE TRIGGER trigger_auto_calculate_discount_on_payments;
        RETURN 'Discount triggers DISABLED';
    END IF;
END;
$$ LANGUAGE plpgsql;

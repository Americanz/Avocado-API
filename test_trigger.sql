-- Тестова функція для діагностики тригера
CREATE OR REPLACE FUNCTION process_bonus_operations()
RETURNS TRIGGER AS $$
BEGIN
    RAISE NOTICE 'BONUS TRIGGER: Викликано для транзакції %', NEW.transaction_id;

    -- Перевіряємо базові умови
    IF NEW.client_id IS NULL THEN
        RAISE NOTICE 'BONUS TRIGGER: Немає client_id';
        RETURN NEW;
    END IF;

    IF NEW.date_close IS NULL THEN
        RAISE NOTICE 'BONUS TRIGGER: Немає date_close';
        RETURN NEW;
    END IF;

    RAISE NOTICE 'BONUS TRIGGER: Всі умови виконані для транзакції %', NEW.transaction_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Тестуємо оновлення транзакції
UPDATE transactions SET updated_at = NOW() WHERE transaction_id = 2598670;

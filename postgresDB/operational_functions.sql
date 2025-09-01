-- Операційні функції для LUCHAN
-- Файл: operational_functions.sql

-- =====================================================
-- 1. Функція для швидкого пошуку транзакцій клієнта
-- =====================================================
CREATE OR REPLACE FUNCTION find_client_transactions(
    search_phone TEXT DEFAULT NULL,
    search_name TEXT DEFAULT NULL,
    limit_count INTEGER DEFAULT 50
)
RETURNS TABLE (
    transaction_id BIGINT,
    client_name TEXT,
    phone TEXT,
    spot_name TEXT,
    transaction_sum NUMERIC(10,2),
    transaction_date TIMESTAMP,
    bonus_used NUMERIC(10,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        pt.transaction_id,
        CONCAT(pc.firstname, ' ', pc.lastname)::TEXT,
        pc.phone::TEXT,
        s.name::TEXT,
        pt.sum::NUMERIC(10,2),
        pt.date_close,
        pt.bonus::NUMERIC(10,2)
    FROM transactions pt
    JOIN clients pc ON pt.client = pc.client_id
    LEFT JOIN spots s ON pt.spot_id = s.spot_id
    WHERE
        (search_phone IS NULL OR pc.phone ILIKE '%' || search_phone || '%')
        AND (search_name IS NULL OR
             CONCAT(pc.firstname, ' ', pc.lastname) ILIKE '%' || search_name || '%')
    ORDER BY pt.date_close DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 2. Функція для аналізу продуктивності точки по годинах
-- =====================================================
CREATE OR REPLACE FUNCTION get_spot_hourly_performance(
    spot_id_param INTEGER,
    analysis_date DATE DEFAULT CURRENT_DATE
)
RETURNS TABLE (
    hour_of_day INTEGER,
    transactions_count BIGINT,
    total_revenue NUMERIC(10,2),
    avg_check NUMERIC(10,2),
    performance_score NUMERIC(5,2)
) AS $$
BEGIN
    RETURN QUERY
    WITH hourly_stats AS (
        SELECT
            EXTRACT(HOUR FROM date_close)::INTEGER as hour_num,
            COUNT(*) as trans_count,
            SUM(sum) as revenue,
            AVG(sum) as avg_check
        FROM transactions
        WHERE spot_id = spot_id_param
            AND DATE(date_close) = analysis_date
        GROUP BY EXTRACT(HOUR FROM date_close)
    ),
    daily_total AS (
        SELECT
            AVG(trans_count) as avg_hourly_trans,
            AVG(revenue) as avg_hourly_revenue
        FROM hourly_stats
    )
    SELECT
        hs.hour_num,
        hs.trans_count,
        hs.revenue::NUMERIC(10,2),
        hs.avg_check::NUMERIC(10,2),
        CASE
            WHEN dt.avg_hourly_revenue > 0
            THEN (hs.revenue / dt.avg_hourly_revenue * 100)::NUMERIC(5,2)
            ELSE 0::NUMERIC(5,2)
        END
    FROM hourly_stats hs
    CROSS JOIN daily_total dt
    ORDER BY hs.hour_num;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 3. Функція для виявлення аномалій в продажах
-- =====================================================
CREATE OR REPLACE FUNCTION detect_sales_anomalies(
    check_date DATE DEFAULT CURRENT_DATE,
    deviation_threshold NUMERIC DEFAULT 2.0
)
RETURNS TABLE (
    spot_id INTEGER,
    spot_name TEXT,
    date_checked DATE,
    actual_revenue NUMERIC(10,2),
    expected_revenue NUMERIC(10,2),
    deviation_percent NUMERIC(5,2),
    anomaly_type TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH historical_averages AS (
        SELECT
            pt.spot_id,
            s.name as spot_name,
            AVG(daily_revenue) as avg_revenue,
            STDDEV(daily_revenue) as stddev_revenue
        FROM (
            SELECT
                spot_id,
                DATE(date_close) as trans_date,
                SUM(sum) as daily_revenue
            FROM transactions
            WHERE DATE(date_close) >= check_date - INTERVAL '30 days'
                AND DATE(date_close) < check_date
            GROUP BY spot_id, DATE(date_close)
        ) daily_stats
        JOIN transactions pt ON daily_stats.spot_id = pt.spot_id
        JOIN spots s ON pt.spot_id = s.spot_id
        GROUP BY pt.spot_id, s.name
    ),
    current_day_stats AS (
        SELECT
            pt.spot_id,
            SUM(pt.sum) as today_revenue
        FROM transactions pt
        WHERE DATE(pt.date_close) = check_date
        GROUP BY pt.spot_id
    )
    SELECT
        ha.spot_id,
        ha.spot_name::TEXT,
        check_date,
        COALESCE(cds.today_revenue, 0)::NUMERIC(10,2),
        ha.avg_revenue::NUMERIC(10,2),
        CASE
            WHEN ha.avg_revenue > 0
            THEN ((COALESCE(cds.today_revenue, 0) - ha.avg_revenue) / ha.avg_revenue * 100)::NUMERIC(5,2)
            ELSE 0::NUMERIC(5,2)
        END,
        CASE
            WHEN COALESCE(cds.today_revenue, 0) > ha.avg_revenue + (deviation_threshold * ha.stddev_revenue)
            THEN 'Високі продажі'
            WHEN COALESCE(cds.today_revenue, 0) < ha.avg_revenue - (deviation_threshold * ha.stddev_revenue)
            THEN 'Низькі продажі'
            ELSE 'Нормальні'
        END::TEXT
    FROM historical_averages ha
    LEFT JOIN current_day_stats cds ON ha.spot_id = cds.spot_id
    WHERE ABS(COALESCE(cds.today_revenue, 0) - ha.avg_revenue) > (deviation_threshold * ha.stddev_revenue)
    ORDER BY ABS(COALESCE(cds.today_revenue, 0) - ha.avg_revenue) DESC;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 4. Функція для аналізу конверсії нових клієнтів
-- =====================================================
CREATE OR REPLACE FUNCTION get_new_client_conversion(
    start_date DATE,
    end_date DATE
)
RETURNS TABLE (
    spot_name TEXT,
    new_clients INTEGER,
    returned_clients INTEGER,
    conversion_rate NUMERIC(5,2),
    avg_first_purchase NUMERIC(10,2),
    avg_second_purchase NUMERIC(10,2)
) AS $$
BEGIN
    RETURN QUERY
    WITH first_visits AS (
        SELECT
            pc.client_id,
            pt.spot_id,
            MIN(pt.date_close) as first_visit_date,
            MIN(pt.sum) as first_purchase_amount
        FROM clients pc
        JOIN transactions pt ON pc.client_id = pt.client
        WHERE pt.date_close >= start_date AND pt.date_close <= end_date
        GROUP BY pc.client_id, pt.spot_id
    ),
    second_visits AS (
        SELECT
            fv.client_id,
            fv.spot_id,
            MIN(pt.sum) as second_purchase_amount
        FROM first_visits fv
        JOIN transactions pt ON fv.client_id = pt.client
        WHERE pt.date_close > fv.first_visit_date
            AND pt.spot_id = fv.spot_id
        GROUP BY fv.client_id, fv.spot_id
    )
    SELECT
        s.name::TEXT,
        COUNT(fv.client_id)::INTEGER,
        COUNT(sv.client_id)::INTEGER,
        CASE
            WHEN COUNT(fv.client_id) > 0
            THEN (COUNT(sv.client_id)::NUMERIC / COUNT(fv.client_id) * 100)::NUMERIC(5,2)
            ELSE 0::NUMERIC(5,2)
        END,
        AVG(fv.first_purchase_amount)::NUMERIC(10,2),
        AVG(sv.second_purchase_amount)::NUMERIC(10,2)
    FROM first_visits fv
    LEFT JOIN second_visits sv ON fv.client_id = sv.client_id
        AND fv.spot_id = sv.spot_id
    JOIN spots s ON fv.spot_id = s.spot_id
    GROUP BY s.name
    ORDER BY COUNT(fv.client_id) DESC;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 5. Функція для розрахунку прогнозу продажів
-- =====================================================
CREATE OR REPLACE FUNCTION forecast_sales(
    spot_id_param INTEGER,
    forecast_days INTEGER DEFAULT 7
)
RETURNS TABLE (
    forecast_date DATE,
    predicted_transactions INTEGER,
    predicted_revenue NUMERIC(10,2),
    confidence_level TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH historical_trends AS (
        SELECT
            EXTRACT(DOW FROM date_close) as day_of_week,
            AVG(daily_transactions) as avg_transactions,
            AVG(daily_revenue) as avg_revenue,
            STDDEV(daily_revenue) as stddev_revenue
        FROM (
            SELECT
                DATE(date_close) as trans_date,
                COUNT(*) as daily_transactions,
                SUM(sum) as daily_revenue
            FROM transactions
            WHERE spot_id = spot_id_param
                AND date_close >= CURRENT_DATE - INTERVAL '60 days'
            GROUP BY DATE(date_close)
        ) daily_stats
        JOIN transactions pt ON DATE(pt.date_close) = daily_stats.trans_date
        WHERE pt.spot_id = spot_id_param
        GROUP BY EXTRACT(DOW FROM pt.date_close)
    )
    SELECT
        (CURRENT_DATE + generate_series(1, forecast_days))::DATE,
        ht.avg_transactions::INTEGER,
        ht.avg_revenue::NUMERIC(10,2),
        CASE
            WHEN ht.stddev_revenue / ht.avg_revenue < 0.2 THEN 'Висока'
            WHEN ht.stddev_revenue / ht.avg_revenue < 0.4 THEN 'Середня'
            ELSE 'Низька'
        END::TEXT
    FROM generate_series(1, forecast_days) as gs
    JOIN historical_trends ht ON ht.day_of_week = EXTRACT(DOW FROM CURRENT_DATE + gs)
    ORDER BY (CURRENT_DATE + gs);
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- КОМЕНТАРІ ДЛЯ ВИКОРИСТАННЯ
-- =====================================================

-- Приклади використання:

-- 1. Пошук транзакцій клієнта за телефоном:
-- SELECT * FROM find_client_transactions('+380501234567');

-- 2. Пошук клієнта за ім'ям:
-- SELECT * FROM find_client_transactions(NULL, 'Іван');

-- 3. Аналіз продуктивності точки по годинах:
-- SELECT * FROM get_spot_hourly_performance(1, '2025-08-31');

-- 4. Виявлення аномалій в продажах:
-- SELECT * FROM detect_sales_anomalies();

-- 5. Аналіз конверсії нових клієнтів за місяць:
-- SELECT * FROM get_new_client_conversion('2025-08-01', '2025-08-31');

-- 6. Прогноз продажів на тиждень:
-- SELECT * FROM forecast_sales(1, 7);

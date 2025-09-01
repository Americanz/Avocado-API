-- PostgreSQL функції для аналітики LUCHAN
-- Файл: business_analytics_functions.sql

-- =====================================================
-- 1. Функція для розрахунку доходу по точці за період
-- =====================================================
CREATE OR REPLACE FUNCTION get_spot_revenue(
    spot_id_param INTEGER,
    start_date DATE,
    end_date DATE
)
RETURNS TABLE (
    spot_name TEXT,
    total_transactions BIGINT,
    total_revenue NUMERIC(10,2),
    avg_check NUMERIC(10,2),
    max_check NUMERIC(10,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        s.name::TEXT,
        COUNT(pt.id),
        COALESCE(SUM(pt.sum), 0)::NUMERIC(10,2),
        COALESCE(AVG(pt.sum), 0)::NUMERIC(10,2),
        COALESCE(MAX(pt.sum), 0)::NUMERIC(10,2)
    FROM spots s
    LEFT JOIN transactions pt ON s.spot_id = pt.spot_id
        AND pt.date_close >= start_date
        AND pt.date_close <= end_date
    WHERE s.spot_id = spot_id_param
    GROUP BY s.name;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 2. Функція для аналізу клієнта
-- =====================================================
CREATE OR REPLACE FUNCTION get_client_analytics(client_id_param BIGINT)
RETURNS TABLE (
    client_name TEXT,
    phone TEXT,
    total_transactions BIGINT,
    total_spent NUMERIC(10,2),
    avg_check NUMERIC(10,2),
    first_purchase TIMESTAMP,
    last_purchase TIMESTAMP,
    days_active INTEGER,
    favorite_spot TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH client_stats AS (
        SELECT
            CONCAT(pc.firstname, ' ', pc.lastname)::TEXT as full_name,
            pc.phone::TEXT,
            COUNT(pt.id) as trans_count,
            COALESCE(SUM(pt.sum), 0)::NUMERIC(10,2) as spent,
            COALESCE(AVG(pt.sum), 0)::NUMERIC(10,2) as avg_check,
            MIN(pt.date_close) as first_date,
            MAX(pt.date_close) as last_date
        FROM clients pc
        LEFT JOIN transactions pt ON pc.client_id = pt.client
        WHERE pc.client_id = client_id_param
        GROUP BY pc.client_id, pc.firstname, pc.lastname, pc.phone
    ),
    favorite_spot_calc AS (
        SELECT
            s.name as spot_name,
            COUNT(*) as visit_count
        FROM transactions pt
        JOIN spots s ON pt.spot_id = s.spot_id
        WHERE pt.client = client_id_param
        GROUP BY s.name
        ORDER BY visit_count DESC
        LIMIT 1
    )
    SELECT
        cs.full_name,
        cs.phone,
        cs.trans_count,
        cs.spent,
        cs.avg_check,
        cs.first_date,
        cs.last_date,
        CASE
            WHEN cs.first_date IS NOT NULL AND cs.last_date IS NOT NULL
            THEN EXTRACT(DAY FROM cs.last_date - cs.first_date)::INTEGER
            ELSE 0
        END,
        COALESCE(fsc.spot_name, 'Немає даних')::TEXT
    FROM client_stats cs
    LEFT JOIN favorite_spot_calc fsc ON true;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 3. Функція для топ продуктів за період
-- =====================================================
CREATE OR REPLACE FUNCTION get_top_products(
    start_date DATE,
    end_date DATE,
    limit_count INTEGER DEFAULT 10
)
RETURNS TABLE (
    product_name TEXT,
    category_name TEXT,
    total_quantity NUMERIC,
    total_revenue NUMERIC(10,2),
    avg_price NUMERIC(10,2),
    order_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.product_name::TEXT,
        p.category_name::TEXT,
        COALESCE(SUM(ptp.count), 0)::NUMERIC,
        COALESCE(SUM(ptp.sum), 0)::NUMERIC(10,2),
        CASE
            WHEN SUM(ptp.count) > 0
            THEN (SUM(ptp.sum) / SUM(ptp.count))::NUMERIC(10,2)
            ELSE 0::NUMERIC(10,2)
        END,
        COUNT(ptp.id)
    FROM products p
    JOIN poster_transaction_products ptp ON p.poster_product_id = ptp.product_id
    JOIN transactions pt ON ptp.transaction_id = pt.transaction_id
    WHERE pt.date_close >= start_date
        AND pt.date_close <= end_date
    GROUP BY p.product_name, p.category_name
    ORDER BY SUM(ptp.sum) DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 4. Функція для аналізу сезонності
-- =====================================================
CREATE OR REPLACE FUNCTION get_seasonal_analytics()
RETURNS TABLE (
    month_name TEXT,
    month_number INTEGER,
    avg_transactions NUMERIC,
    avg_revenue NUMERIC(10,2),
    seasonality_index NUMERIC(5,2)
) AS $$
BEGIN
    RETURN QUERY
    WITH monthly_stats AS (
        SELECT
            EXTRACT(MONTH FROM date_close)::INTEGER as month_num,
            EXTRACT(YEAR FROM date_close) as year_num,
            COUNT(*) as transactions,
            SUM(sum) as revenue
        FROM transactions
        WHERE date_close >= CURRENT_DATE - INTERVAL '2 years'
        GROUP BY EXTRACT(YEAR FROM date_close), EXTRACT(MONTH FROM date_close)
    ),
    monthly_averages AS (
        SELECT
            month_num,
            AVG(transactions)::NUMERIC as avg_trans,
            AVG(revenue)::NUMERIC(10,2) as avg_rev
        FROM monthly_stats
        GROUP BY month_num
    ),
    overall_average AS (
        SELECT AVG(avg_trans) as overall_avg_trans
        FROM monthly_averages
    )
    SELECT
        CASE ma.month_num
            WHEN 1 THEN 'Січень'
            WHEN 2 THEN 'Лютий'
            WHEN 3 THEN 'Березень'
            WHEN 4 THEN 'Квітень'
            WHEN 5 THEN 'Травень'
            WHEN 6 THEN 'Червень'
            WHEN 7 THEN 'Липень'
            WHEN 8 THEN 'Серпень'
            WHEN 9 THEN 'Вересень'
            WHEN 10 THEN 'Жовтень'
            WHEN 11 THEN 'Листопад'
            WHEN 12 THEN 'Грудень'
        END::TEXT,
        ma.month_num,
        ma.avg_trans,
        ma.avg_rev,
        CASE
            WHEN oa.overall_avg_trans > 0
            THEN (ma.avg_trans / oa.overall_avg_trans * 100)::NUMERIC(5,2)
            ELSE 0::NUMERIC(5,2)
        END
    FROM monthly_averages ma
    CROSS JOIN overall_average oa
    ORDER BY ma.month_num;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 5. Функція для RFM аналізу клієнтів
-- =====================================================
CREATE OR REPLACE FUNCTION get_rfm_analysis()
RETURNS TABLE (
    client_id BIGINT,
    client_name TEXT,
    phone TEXT,
    recency_score INTEGER,
    frequency_score INTEGER,
    monetary_score INTEGER,
    rfm_segment TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH client_metrics AS (
        SELECT
            pc.client_id,
            CONCAT(pc.firstname, ' ', pc.lastname)::TEXT as full_name,
            pc.phone::TEXT,
            EXTRACT(DAY FROM CURRENT_DATE - MAX(pt.date_close))::INTEGER as recency_days,
            COUNT(pt.id) as frequency,
            COALESCE(SUM(pt.sum), 0) as monetary
        FROM clients pc
        LEFT JOIN transactions pt ON pc.client_id = pt.client
        GROUP BY pc.client_id, pc.firstname, pc.lastname, pc.phone
        HAVING COUNT(pt.id) > 0
    ),
    rfm_scores AS (
        SELECT
            client_id,
            full_name,
            phone,
            CASE
                WHEN recency_days <= 30 THEN 5
                WHEN recency_days <= 60 THEN 4
                WHEN recency_days <= 90 THEN 3
                WHEN recency_days <= 180 THEN 2
                ELSE 1
            END as r_score,
            CASE
                WHEN frequency >= 10 THEN 5
                WHEN frequency >= 7 THEN 4
                WHEN frequency >= 5 THEN 3
                WHEN frequency >= 3 THEN 2
                ELSE 1
            END as f_score,
            CASE
                WHEN monetary >= 5000 THEN 5
                WHEN monetary >= 2000 THEN 4
                WHEN monetary >= 1000 THEN 3
                WHEN monetary >= 500 THEN 2
                ELSE 1
            END as m_score
        FROM client_metrics
    )
    SELECT
        rs.client_id,
        rs.full_name,
        rs.phone,
        rs.r_score,
        rs.f_score,
        rs.m_score,
        CASE
            WHEN rs.r_score >= 4 AND rs.f_score >= 4 AND rs.m_score >= 4 THEN 'Champions'
            WHEN rs.r_score >= 3 AND rs.f_score >= 4 AND rs.m_score >= 4 THEN 'Loyal Customers'
            WHEN rs.r_score >= 4 AND rs.f_score <= 2 AND rs.m_score >= 3 THEN 'Potential Loyalists'
            WHEN rs.r_score >= 4 AND rs.f_score <= 2 AND rs.m_score <= 2 THEN 'New Customers'
            WHEN rs.r_score >= 3 AND rs.f_score >= 3 AND rs.m_score >= 3 THEN 'Promising'
            WHEN rs.r_score <= 2 AND rs.f_score >= 3 AND rs.m_score >= 3 THEN 'Need Attention'
            WHEN rs.r_score <= 2 AND rs.f_score <= 2 AND rs.m_score >= 4 THEN 'About to Sleep'
            WHEN rs.r_score <= 2 AND rs.f_score >= 4 AND rs.m_score <= 2 THEN 'At Risk'
            WHEN rs.r_score <= 1 AND rs.f_score >= 4 AND rs.m_score >= 4 THEN 'Cannot Lose Them'
            WHEN rs.r_score <= 2 AND rs.f_score <= 2 AND rs.m_score <= 2 THEN 'Hibernating'
            ELSE 'Lost'
        END::TEXT
    FROM rfm_scores rs
    ORDER BY rs.m_score DESC, rs.f_score DESC, rs.r_score DESC;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- КОМЕНТАРІ ДЛЯ ВИКОРИСТАННЯ ФУНКЦІЙ
-- =====================================================

-- Приклади використання:

-- 1. Аналіз доходу точки за липень 2025:
-- SELECT * FROM get_spot_revenue(1, '2025-07-01', '2025-07-31');

-- 2. Повний аналіз клієнта:
-- SELECT * FROM get_client_analytics(123);

-- 3. Топ-10 продуктів за серпень 2025:
-- SELECT * FROM get_top_products('2025-08-01', '2025-08-31', 10);

-- 4. Сезонний аналіз:
-- SELECT * FROM get_seasonal_analytics();

-- 5. RFM сегментація клієнтів:
-- SELECT * FROM get_rfm_analysis();

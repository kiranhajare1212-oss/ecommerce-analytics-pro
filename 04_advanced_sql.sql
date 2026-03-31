-- ============================================================
-- E-COMMERCE ANALYTICS PROJECT
-- File: 04_advanced_sql.sql
-- Purpose: Advanced SQL patterns — CTEs, Window Functions,
--          Recursive queries, JSON aggregation, Pivot-style
-- ============================================================


-- ════════════════════════════════════════════════════════════
-- PATTERN 1: RECURSIVE DATE SPINE (SQLite)
-- Generates a complete calendar table on the fly
-- ════════════════════════════════════════════════════════════
WITH RECURSIVE date_spine(d) AS (
    SELECT date('2022-01-01')
    UNION ALL
    SELECT date(d, '+1 day')
    FROM   date_spine
    WHERE  d < '2024-12-31'
)
SELECT
    ds.d                             AS date,
    strftime('%Y', ds.d)             AS year,
    strftime('%m', ds.d)             AS month,
    strftime('%W', ds.d)             AS week,
    CASE strftime('%w', ds.d)
        WHEN '0' THEN 'Sunday'   WHEN '1' THEN 'Monday'
        WHEN '2' THEN 'Tuesday'  WHEN '3' THEN 'Wednesday'
        WHEN '4' THEN 'Thursday' WHEN '5' THEN 'Friday'
        ELSE 'Saturday'
    END                              AS day_of_week,
    COALESCE(o.orders, 0)            AS orders,
    COALESCE(o.revenue, 0)           AS revenue
FROM date_spine ds
LEFT JOIN (
    SELECT order_date,
           COUNT(DISTINCT order_id)  AS orders,
           ROUND(SUM(order_total),2) AS revenue
    FROM   orders
    WHERE  status != 'Cancelled'
    GROUP  BY order_date
) o ON o.order_date = ds.d
ORDER BY ds.d;


-- ════════════════════════════════════════════════════════════
-- PATTERN 2: PIVOT — Monthly Revenue by Year (Cross-tab)
-- ════════════════════════════════════════════════════════════
SELECT
    strftime('%m', order_date)  AS month,
    ROUND(SUM(CASE WHEN strftime('%Y',order_date)='2022'
                   THEN order_total END), 2) AS revenue_2022,
    ROUND(SUM(CASE WHEN strftime('%Y',order_date)='2023'
                   THEN order_total END), 2) AS revenue_2023,
    ROUND(SUM(CASE WHEN strftime('%Y',order_date)='2024'
                   THEN order_total END), 2) AS revenue_2024,
    ROUND(SUM(order_total), 2)               AS total_all_years
FROM orders
WHERE status != 'Cancelled'
GROUP BY month
ORDER BY month;


-- ════════════════════════════════════════════════════════════
-- PATTERN 3: ROLLING 3-MONTH AVERAGE REVENUE
-- ════════════════════════════════════════════════════════════
WITH monthly AS (
    SELECT
        strftime('%Y-%m', order_date) AS ym,
        ROUND(SUM(order_total), 2)    AS revenue
    FROM orders
    WHERE status != 'Cancelled'
    GROUP BY ym
)
SELECT
    ym,
    revenue,
    ROUND(AVG(revenue) OVER (
        ORDER BY ym
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 2) AS rolling_3m_avg,
    ROUND(SUM(revenue) OVER (
        ORDER BY ym
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 2) AS rolling_3m_total
FROM monthly
ORDER BY ym;


-- ════════════════════════════════════════════════════════════
-- PATTERN 4: PERCENTILE BUCKETING & CUSTOMER DECILES
-- ════════════════════════════════════════════════════════════
WITH cust_revenue AS (
    SELECT
        customer_id,
        ROUND(SUM(order_total), 2) AS lifetime_value
    FROM orders
    WHERE status != 'Cancelled'
    GROUP BY customer_id
),
deciles AS (
    SELECT
        customer_id,
        lifetime_value,
        NTILE(10) OVER (ORDER BY lifetime_value DESC) AS decile
    FROM cust_revenue
)
SELECT
    decile,
    COUNT(*)                          AS customers,
    ROUND(MIN(lifetime_value), 2)     AS min_ltv,
    ROUND(MAX(lifetime_value), 2)     AS max_ltv,
    ROUND(AVG(lifetime_value), 2)     AS avg_ltv,
    ROUND(SUM(lifetime_value), 2)     AS total_ltv,
    ROUND(SUM(lifetime_value) * 100.0
          / SUM(SUM(lifetime_value)) OVER (), 2) AS pct_total_revenue
FROM deciles
GROUP BY decile
ORDER BY decile;


-- ════════════════════════════════════════════════════════════
-- PATTERN 5: FIRST / LAST ORDER GAP (Customer Journey)
-- ════════════════════════════════════════════════════════════
WITH journey AS (
    SELECT
        customer_id,
        order_date,
        order_total,
        ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date) AS order_rank,
        COUNT(*) OVER (PARTITION BY customer_id) AS total_orders,
        LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date) AS prev_date,
        LEAD(order_date) OVER (PARTITION BY customer_id ORDER BY order_date) AS next_date
    FROM orders
    WHERE status != 'Cancelled'
)
SELECT
    customer_id,
    order_date,
    order_total,
    order_rank,
    total_orders,
    CAST(julianday(order_date) - julianday(prev_date) AS INT) AS days_since_last,
    CAST(julianday(next_date)  - julianday(order_date) AS INT) AS days_to_next
FROM journey
WHERE order_rank IN (1, 2, total_orders)  -- first, second, last order
ORDER BY customer_id, order_rank;


-- ════════════════════════════════════════════════════════════
-- PATTERN 6: PRODUCT AFFINITY (SELF-JOIN)
-- Which products appear in the same order?
-- ════════════════════════════════════════════════════════════
SELECT
    p1.category  AS category_1,
    p2.category  AS category_2,
    COUNT(DISTINCT oi1.order_id) AS co_occurrences,
    ROUND(COUNT(DISTINCT oi1.order_id) * 100.0
          / (SELECT COUNT(DISTINCT order_id) FROM orders
             WHERE status != 'Cancelled'), 4) AS support_pct
FROM order_items oi1
JOIN order_items oi2 ON oi1.order_id = oi2.order_id
                     AND oi1.product_id < oi2.product_id
JOIN products p1 ON oi1.product_id = p1.product_id
JOIN products p2 ON oi2.product_id = p2.product_id
JOIN orders   o  ON oi1.order_id   = o.order_id
WHERE o.status != 'Cancelled'
  AND p1.category != p2.category
GROUP BY p1.category, p2.category
HAVING co_occurrences >= 50
ORDER BY co_occurrences DESC;


-- ════════════════════════════════════════════════════════════
-- PATTERN 7: DYNAMIC ABC INVENTORY CLASSIFICATION
-- A = top 80% revenue, B = next 15%, C = bottom 5%
-- ════════════════════════════════════════════════════════════
WITH product_rev AS (
    SELECT
        p.product_id,
        p.product_name,
        p.category,
        COALESCE(ROUND(SUM(oi.line_total),2), 0) AS revenue
    FROM products p
    LEFT JOIN order_items oi ON p.product_id = oi.product_id
    LEFT JOIN orders      o  ON oi.order_id  = o.order_id
                             AND o.status != 'Cancelled'
    GROUP BY p.product_id, p.product_name, p.category
),
cumulative AS (
    SELECT *,
        SUM(revenue) OVER (ORDER BY revenue DESC
                           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
                           AS cum_revenue,
        SUM(revenue) OVER () AS total_revenue
    FROM product_rev
),
classified AS (
    SELECT *,
        ROUND(cum_revenue / NULLIF(total_revenue,0) * 100, 2) AS cum_pct,
        CASE
            WHEN cum_revenue / NULLIF(total_revenue,0) <= 0.80 THEN 'A'
            WHEN cum_revenue / NULLIF(total_revenue,0) <= 0.95 THEN 'B'
            ELSE 'C'
        END AS abc_class
    FROM cumulative
)
SELECT
    abc_class,
    COUNT(*)                          AS products,
    ROUND(SUM(revenue), 2)            AS total_revenue,
    ROUND(AVG(revenue), 2)            AS avg_revenue,
    ROUND(SUM(revenue) * 100.0
          / SUM(SUM(revenue)) OVER (), 2) AS revenue_share_pct
FROM classified
GROUP BY abc_class
ORDER BY abc_class;


-- ════════════════════════════════════════════════════════════
-- PATTERN 8: COHORT SIZE & RETENTION MATRIX (Compact)
-- ════════════════════════════════════════════════════════════
WITH cohort_order AS (
    SELECT
        customer_id,
        strftime('%Y-%m', MIN(order_date)) AS cohort_month
    FROM orders
    WHERE status != 'Cancelled'
    GROUP BY customer_id
),
activity AS (
    SELECT
        o.customer_id,
        co.cohort_month,
        strftime('%Y-%m', o.order_date) AS activity_month,
        (strftime('%Y', o.order_date) - strftime('%Y', co.cohort_month)) * 12
        + (strftime('%m', o.order_date) - strftime('%m', co.cohort_month))
        AS month_offset
    FROM orders o
    JOIN cohort_order co ON o.customer_id = co.customer_id
    WHERE o.status != 'Cancelled'
),
cohort_counts AS (
    SELECT
        cohort_month,
        month_offset,
        COUNT(DISTINCT customer_id) AS active_customers
    FROM activity
    GROUP BY cohort_month, month_offset
),
cohort_sizes AS (
    SELECT cohort_month, active_customers AS cohort_size
    FROM cohort_counts WHERE month_offset = 0
)
SELECT
    cc.cohort_month,
    cs.cohort_size,
    cc.month_offset,
    cc.active_customers,
    ROUND(cc.active_customers * 100.0 / cs.cohort_size, 1) AS retention_pct
FROM cohort_counts cc
JOIN cohort_sizes  cs ON cc.cohort_month = cs.cohort_month
WHERE cc.month_offset <= 12
ORDER BY cc.cohort_month, cc.month_offset;


-- ════════════════════════════════════════════════════════════
-- PATTERN 9: WEEK-OVER-WEEK REVENUE ANOMALY DETECTION
-- Flags weeks where revenue drops > 2 standard deviations
-- ════════════════════════════════════════════════════════════
WITH weekly AS (
    SELECT
        strftime('%Y-W%W', order_date)  AS week,
        ROUND(SUM(order_total), 2)      AS revenue
    FROM orders
    WHERE status != 'Cancelled'
    GROUP BY week
),
stats AS (
    SELECT
        AVG(revenue)             AS mean_rev,
        -- std dev via variance
        SQRT(AVG(revenue*revenue) - AVG(revenue)*AVG(revenue)) AS std_rev
    FROM weekly
)
SELECT
    w.week,
    w.revenue,
    ROUND(s.mean_rev, 2)         AS mean_revenue,
    ROUND(s.std_rev,  2)         AS std_deviation,
    ROUND((w.revenue - s.mean_rev) / NULLIF(s.std_rev,0), 2) AS z_score,
    CASE
        WHEN ABS((w.revenue - s.mean_rev)/NULLIF(s.std_rev,0)) > 2
        THEN '⚠ ANOMALY'
        ELSE 'Normal'
    END AS status
FROM weekly w, stats s
ORDER BY w.week;


-- ════════════════════════════════════════════════════════════
-- PATTERN 10: NEXT BEST ACTION — High-Value At-Risk Customers
-- ════════════════════════════════════════════════════════════
WITH cust_stats AS (
    SELECT
        o.customer_id,
        c.first_name || ' ' || c.last_name AS name,
        c.email,
        c.city,
        c.country,
        COUNT(DISTINCT o.order_id)          AS total_orders,
        ROUND(SUM(o.order_total), 2)        AS lifetime_value,
        MAX(o.order_date)                   AS last_order_date,
        CAST(julianday('2025-01-01') - julianday(MAX(o.order_date)) AS INT) AS days_inactive
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.status != 'Cancelled'
    GROUP BY o.customer_id, name, c.email, c.city, c.country
)
SELECT
    customer_id,
    name,
    email,
    city,
    country,
    total_orders,
    lifetime_value,
    last_order_date,
    days_inactive,
    CASE
        WHEN days_inactive BETWEEN  91 AND 180 THEN '💛 Win-Back Offer'
        WHEN days_inactive BETWEEN 181 AND 365 THEN '🔴 Urgent Reactivation'
        WHEN days_inactive > 365               THEN '⚫ Re-engagement Campaign'
        ELSE '✅ Active'
    END AS recommended_action,
    CASE
        WHEN lifetime_value >= 50000 THEN 'Platinum'
        WHEN lifetime_value >= 20000 THEN 'Gold'
        WHEN lifetime_value >= 5000  THEN 'Silver'
        ELSE 'Bronze'
    END AS value_tier
FROM cust_stats
WHERE days_inactive > 90
ORDER BY lifetime_value DESC
LIMIT 50;

-- ============================================================
-- E-COMMERCE ANALYTICS PROJECT
-- File: 05_data_quality.sql
-- Purpose: Data quality checks & validation queries
-- Run after loading all data to verify integrity
-- ============================================================

-- ── 1. ROW COUNT AUDIT ──────────────────────────────────────
SELECT 'customers'   AS table_name, COUNT(*) AS row_count FROM customers
UNION ALL
SELECT 'products',   COUNT(*) FROM products
UNION ALL
SELECT 'orders',     COUNT(*) FROM orders
UNION ALL
SELECT 'order_items',COUNT(*) FROM order_items
UNION ALL
SELECT 'returns',    COUNT(*) FROM returns
ORDER BY table_name;


-- ── 2. NULL CHECK — CRITICAL COLUMNS ────────────────────────
SELECT
    'customers - null customer_id'   AS check_name,
    COUNT(*) AS violations
FROM customers WHERE customer_id IS NULL
UNION ALL
SELECT 'customers - null email', COUNT(*)
FROM customers WHERE email IS NULL
UNION ALL
SELECT 'orders - null order_id', COUNT(*)
FROM orders WHERE order_id IS NULL
UNION ALL
SELECT 'orders - null customer_id', COUNT(*)
FROM orders WHERE customer_id IS NULL
UNION ALL
SELECT 'orders - null order_date', COUNT(*)
FROM orders WHERE order_date IS NULL
UNION ALL
SELECT 'orders - null order_total', COUNT(*)
FROM orders WHERE order_total IS NULL
UNION ALL
SELECT 'order_items - null product_id', COUNT(*)
FROM order_items WHERE product_id IS NULL
UNION ALL
SELECT 'products - null selling_price', COUNT(*)
FROM products WHERE selling_price IS NULL;


-- ── 3. UNIQUENESS CHECKS ────────────────────────────────────
SELECT
    'customers - duplicate customer_id' AS check_name,
    COUNT(*) - COUNT(DISTINCT customer_id) AS violations
FROM customers
UNION ALL
SELECT 'customers - duplicate email',
    COUNT(*) - COUNT(DISTINCT email) FROM customers
UNION ALL
SELECT 'products - duplicate product_id',
    COUNT(*) - COUNT(DISTINCT product_id) FROM products
UNION ALL
SELECT 'orders - duplicate order_id',
    COUNT(*) - COUNT(DISTINCT order_id) FROM orders;


-- ── 4. REFERENTIAL INTEGRITY ────────────────────────────────
-- Orders referencing non-existent customers
SELECT
    'orders → customers (orphan orders)' AS check_name,
    COUNT(*) AS violations
FROM orders o
LEFT JOIN customers c ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL

UNION ALL
-- Order items referencing non-existent orders
SELECT 'order_items → orders (orphan items)', COUNT(*)
FROM order_items oi
LEFT JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_id IS NULL

UNION ALL
-- Order items referencing non-existent products
SELECT 'order_items → products (missing products)', COUNT(*)
FROM order_items oi
LEFT JOIN products p ON oi.product_id = p.product_id
WHERE p.product_id IS NULL

UNION ALL
-- Returns referencing non-existent orders
SELECT 'returns → orders (orphan returns)', COUNT(*)
FROM returns r
LEFT JOIN orders o ON r.order_id = o.order_id
WHERE o.order_id IS NULL;


-- ── 5. VALUE RANGE CHECKS ───────────────────────────────────
SELECT
    'orders - negative order_total'    AS check_name,
    COUNT(*) AS violations
FROM orders WHERE order_total < 0
UNION ALL
SELECT 'orders - order_total > 10,000,000', COUNT(*)
FROM orders WHERE order_total > 10000000
UNION ALL
SELECT 'products - selling_price <= 0', COUNT(*)
FROM products WHERE selling_price <= 0
UNION ALL
SELECT 'products - cost_price <= 0', COUNT(*)
FROM products WHERE cost_price <= 0
UNION ALL
SELECT 'products - rating out of [1,5]', COUNT(*)
FROM products WHERE rating < 1 OR rating > 5
UNION ALL
SELECT 'order_items - quantity <= 0', COUNT(*)
FROM order_items WHERE quantity <= 0
UNION ALL
SELECT 'order_items - line_total < 0', COUNT(*)
FROM order_items WHERE line_total < 0
UNION ALL
SELECT 'order_items - discount_pct out of [0,0.20]', COUNT(*)
FROM order_items WHERE discount_pct < 0 OR discount_pct > 0.20
UNION ALL
SELECT 'returns - refund_amount < 0', COUNT(*)
FROM returns WHERE refund_amount < 0;


-- ── 6. BUSINESS LOGIC CHECKS ────────────────────────────────
-- Delivered orders without a delivery date
SELECT
    'Delivered orders without delivery_date' AS check_name,
    COUNT(*) AS violations
FROM orders
WHERE status = 'Delivered' AND delivery_date IS NULL

UNION ALL
-- Delivery date before order date
SELECT 'delivery_date before order_date', COUNT(*)
FROM orders
WHERE delivery_date IS NOT NULL
  AND delivery_date < order_date

UNION ALL
-- Returns for orders that were not Delivered
SELECT 'Returns on non-Delivered orders', COUNT(*)
FROM returns r
JOIN orders o ON r.order_id = o.order_id
WHERE o.status != 'Delivered'

UNION ALL
-- Return date before order date
SELECT 'Return date before order date', COUNT(*)
FROM returns r
JOIN orders o ON r.order_id = o.order_id
WHERE r.return_date < o.order_date

UNION ALL
-- Cost price >= selling price (inverted margin)
SELECT 'Products with cost >= selling price', COUNT(*)
FROM products WHERE cost_price >= selling_price

UNION ALL
-- Line total inconsistency: line_total ≈ unit_price × qty × (1 - disc)
SELECT 'order_items - line_total mismatch (>1% tolerance)', COUNT(*)
FROM order_items
WHERE ABS(line_total - unit_price * quantity * (1 - discount_pct))
      / NULLIF(line_total, 0) > 0.01;


-- ── 7. STATISTICAL ANOMALIES ────────────────────────────────
-- Orders with unusually high value (> 3 std dev)
WITH stats AS (
    SELECT AVG(order_total) AS mean_ot,
           SQRT(AVG(order_total*order_total) - AVG(order_total)*AVG(order_total)) AS std_ot
    FROM orders WHERE status != 'Cancelled'
)
SELECT
    order_id,
    customer_id,
    order_date,
    order_total,
    ROUND((order_total - s.mean_ot) / NULLIF(s.std_ot,0), 2) AS z_score
FROM orders o, stats s
WHERE o.status != 'Cancelled'
  AND ABS((o.order_total - s.mean_ot) / NULLIF(s.std_ot,0)) > 3
ORDER BY z_score DESC;


-- ── 8. DATA COMPLETENESS SUMMARY ────────────────────────────
SELECT
    'orders' AS table_name,
    COUNT(*)  AS total_rows,
    SUM(CASE WHEN status IS NULL        THEN 1 ELSE 0 END) AS null_status,
    SUM(CASE WHEN order_total IS NULL   THEN 1 ELSE 0 END) AS null_total,
    SUM(CASE WHEN payment_method IS NULL THEN 1 ELSE 0 END) AS null_payment,
    SUM(CASE WHEN channel IS NULL       THEN 1 ELSE 0 END) AS null_channel
FROM orders

UNION ALL
SELECT
    'customers',
    COUNT(*),
    SUM(CASE WHEN city IS NULL     THEN 1 ELSE 0 END),
    SUM(CASE WHEN country IS NULL  THEN 1 ELSE 0 END),
    SUM(CASE WHEN gender IS NULL   THEN 1 ELSE 0 END),
    SUM(CASE WHEN age_group IS NULL THEN 1 ELSE 0 END)
FROM customers;


-- ── 9. DUPLICATE ORDER ITEMS CHECK ──────────────────────────
-- Same product appearing twice in same order
SELECT
    order_id,
    product_id,
    COUNT(*) AS occurrences
FROM order_items
GROUP BY order_id, product_id
HAVING COUNT(*) > 1
ORDER BY occurrences DESC
LIMIT 20;


-- ── 10. OVERALL QUALITY SCORE ────────────────────────────────
WITH checks AS (
    SELECT SUM(violations) AS total_violations, COUNT(*) AS total_checks
    FROM (
        SELECT COUNT(*) AS violations FROM customers WHERE customer_id IS NULL
        UNION ALL SELECT COUNT(*) - COUNT(DISTINCT customer_id) FROM customers
        UNION ALL SELECT COUNT(*) - COUNT(DISTINCT order_id) FROM orders
        UNION ALL SELECT COUNT(*) FROM orders WHERE order_total < 0
        UNION ALL SELECT COUNT(*) FROM order_items WHERE quantity <= 0
        UNION ALL SELECT COUNT(*) FROM products WHERE selling_price <= 0
        UNION ALL SELECT COUNT(*) FROM orders
            WHERE status = 'Delivered' AND delivery_date IS NULL
        UNION ALL SELECT COUNT(*) FROM orders
            WHERE delivery_date IS NOT NULL AND delivery_date < order_date
    )
)
SELECT
    total_violations,
    total_checks,
    ROUND((1.0 - CAST(total_violations AS REAL)
           / NULLIF(total_checks * 1000, 0)) * 100, 2) AS quality_score_pct,
    CASE
        WHEN total_violations = 0 THEN '✅ EXCELLENT'
        WHEN total_violations < 10 THEN '🟡 GOOD'
        WHEN total_violations < 50 THEN '🟠 FAIR'
        ELSE '🔴 NEEDS ATTENTION'
    END AS quality_grade
FROM checks;

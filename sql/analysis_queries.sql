-- ============================================================
-- E-Commerce Sales Dashboard — Analytical SQL Layer
-- Target: MySQL 8.0+ / SQLite (window functions supported in both)
-- Table: fact_transactions (see etl/data_dictionary.md)
-- ============================================================

-- ------------------------------------------------------------
-- 1. Monthly revenue trend with month-over-month growth (window function: LAG)
-- ------------------------------------------------------------
WITH monthly_revenue AS (
    SELECT
        order_month,
        SUM(net_revenue)                       AS revenue,
        COUNT(DISTINCT order_id)               AS orders,
        SUM(net_revenue) / COUNT(DISTINCT order_id) AS avg_order_value
    FROM fact_transactions
    GROUP BY order_month
)
SELECT
    order_month,
    revenue,
    orders,
    ROUND(avg_order_value, 2)                                  AS avg_order_value,
    ROUND(revenue - LAG(revenue) OVER (ORDER BY order_month), 2)      AS revenue_change,
    ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY order_month))
          / LAG(revenue) OVER (ORDER BY order_month), 2)              AS mom_growth_pct
FROM monthly_revenue
ORDER BY order_month;


-- ------------------------------------------------------------
-- 2. Top-performing SKUs per category, ranked (window function: RANK)
-- ------------------------------------------------------------
WITH sku_performance AS (
    SELECT
        category,
        sku,
        SUM(net_revenue)            AS total_revenue,
        SUM(quantity)               AS units_sold,
        COUNT(DISTINCT order_id)    AS orders
    FROM fact_transactions
    GROUP BY category, sku
),
ranked AS (
    SELECT
        *,
        RANK() OVER (PARTITION BY category ORDER BY total_revenue DESC) AS revenue_rank
    FROM sku_performance
)
SELECT category, sku, total_revenue, units_sold, orders, revenue_rank
FROM ranked
WHERE revenue_rank <= 3
ORDER BY category, revenue_rank;


-- ------------------------------------------------------------
-- 3. Regional performance with running (cumulative) revenue total
-- ------------------------------------------------------------
WITH regional_monthly AS (
    SELECT region, order_month, SUM(net_revenue) AS revenue
    FROM fact_transactions
    GROUP BY region, order_month
)
SELECT
    region,
    order_month,
    revenue,
    SUM(revenue) OVER (PARTITION BY region ORDER BY order_month) AS cumulative_revenue,
    ROUND(100.0 * revenue / SUM(revenue) OVER (PARTITION BY order_month), 2) AS pct_of_month_total
FROM regional_monthly
ORDER BY region, order_month;


-- ------------------------------------------------------------
-- 4. Customer value segmentation (RFM-lite) using NTILE window function
-- ------------------------------------------------------------
WITH customer_agg AS (
    SELECT
        customer_id,
        COUNT(DISTINCT order_id)      AS order_count,
        SUM(net_revenue)              AS lifetime_value,
        MAX(order_date)               AS last_order_date
    FROM fact_transactions
    GROUP BY customer_id
)
SELECT
    customer_id,
    order_count,
    lifetime_value,
    last_order_date,
    NTILE(4) OVER (ORDER BY lifetime_value DESC) AS value_quartile   -- 1 = top spenders
FROM customer_agg
ORDER BY lifetime_value DESC;


-- ------------------------------------------------------------
-- 5. Return-rate analysis by category vs. company average (window function: AVG OVER)
-- ------------------------------------------------------------
SELECT
    category,
    COUNT(*)                                              AS total_orders,
    SUM(is_returned)                                       AS returned_orders,
    ROUND(100.0 * SUM(is_returned) / COUNT(*), 2)          AS return_rate_pct,
    ROUND(100.0 * AVG(SUM(is_returned) * 1.0 / COUNT(*)) OVER (), 2) AS company_avg_return_rate_pct
FROM fact_transactions
GROUP BY category
ORDER BY return_rate_pct DESC;


-- ------------------------------------------------------------
-- 6. Channel x payment-method mix, revenue share
-- ------------------------------------------------------------
SELECT
    channel,
    payment_method,
    SUM(net_revenue)                                          AS revenue,
    COUNT(DISTINCT order_id)                                  AS orders,
    ROUND(100.0 * SUM(net_revenue) / SUM(SUM(net_revenue)) OVER (), 2) AS pct_of_total_revenue
FROM fact_transactions
GROUP BY channel, payment_method
ORDER BY revenue DESC;

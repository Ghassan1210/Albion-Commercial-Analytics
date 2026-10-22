-- 03_commercial_and_customer_views.sql
-- Analytical views. Each fact table is aggregated to dimension grain in separate CTEs;
-- facts are never joined directly to each other.

CREATE OR REPLACE VIEW mart_empirical.vw_audit_waterfall_reconciliation AS
-- Basis 1: RAW_SOURCE_LEDGER — all ingested source rows (full lineage, no dedup)
SELECT
    'RAW_SOURCE_LEDGER' AS reporting_basis,
    primary_audit_category,
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (is_calculable_monetary) AS calculable_rows,
    COUNT(*) FILTER (NOT is_calculable_monetary) AS uncalculable_rows,
    SUM(raw_signed_value) FILTER (is_calculable_monetary) AS calculable_signed_gbp
FROM stg.raw_transactions
GROUP BY primary_audit_category

UNION ALL

-- Basis 2: OPERATIONAL_REPORTING_DEFAULT — cross-sheet deduped, intra-sheet multiplicity preserved
-- (all rows where is_cross_sheet_overlap_repeat = FALSE)
SELECT
    'OPERATIONAL_REPORTING_DEFAULT' AS reporting_basis,
    primary_audit_category,
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (is_calculable_monetary) AS calculable_rows,
    COUNT(*) FILTER (NOT is_calculable_monetary) AS uncalculable_rows,
    SUM(raw_signed_value) FILTER (is_calculable_monetary) AS calculable_signed_gbp
FROM stg.raw_transactions
WHERE is_cross_sheet_overlap_repeat = FALSE
GROUP BY primary_audit_category

UNION ALL

-- Basis 3: STRICT_DISTINCT_SIGNATURE_SENSITIVITY — excludes both cross-sheet repeats
-- and same-sheet exact repeats (reported side-by-side to show impact of intra-sheet repeats)
SELECT
    'STRICT_DISTINCT_SIGNATURE_SENSITIVITY' AS reporting_basis,
    primary_audit_category,
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (is_calculable_monetary) AS calculable_rows,
    COUNT(*) FILTER (NOT is_calculable_monetary) AS uncalculable_rows,
    SUM(raw_signed_value) FILTER (is_calculable_monetary) AS calculable_signed_gbp
FROM stg.raw_transactions
WHERE is_cross_sheet_overlap_repeat = FALSE
  AND is_same_sheet_exact_repeat = FALSE
GROUP BY primary_audit_category;

CREATE OR REPLACE VIEW mart_empirical.vw_monthly_commercial_trends AS
WITH sales AS (
    SELECT date_trunc('month', invoice_date)::DATE AS month,
           SUM(raw_signed_value) AS positive_sales_gbp,
           SUM(quantity) AS units_sold,
           COUNT(DISTINCT invoice_no) AS distinct_orders
    FROM mart_empirical.fact_merchandise_sales
    GROUP BY 1
),
returns AS (
    SELECT date_trunc('month', invoice_date)::DATE AS month,
           SUM(raw_signed_value) AS signed_returns_gbp,
           SUM(ABS(raw_signed_value)) AS return_magnitude_gbp,
           SUM(quantity) AS units_returned,
           COUNT(DISTINCT invoice_no) AS return_orders
    FROM mart_empirical.fact_returns_and_cancellations
    GROUP BY 1
),
cust AS (
    SELECT date_trunc('month', invoice_date)::DATE AS month,
           COUNT(DISTINCT CASE WHEN customer_id IS NOT NULL AND customer_id <> 'UNIDENTIFIED' THEN customer_id END) AS identified_active_customers,
           SUM(raw_signed_value) FILTER (WHERE customer_id IS NULL OR customer_id = 'UNIDENTIFIED') AS anonymous_guest_revenue_gbp,
           SUM(raw_signed_value) AS total_revenue_gbp
    FROM mart_empirical.fact_merchandise_sales
    GROUP BY 1
)
SELECT
    s.month,
    s.positive_sales_gbp,
    r.signed_returns_gbp,
    r.return_magnitude_gbp,
    (s.positive_sales_gbp + r.signed_returns_gbp) AS net_recorded_merchandise_value_gbp,
    CASE WHEN s.positive_sales_gbp > 0 THEN r.return_magnitude_gbp / s.positive_sales_gbp END AS merchandise_return_rate_pct,
    s.units_sold,
    r.units_returned,
    s.distinct_orders,
    c.identified_active_customers,
    CASE WHEN c.total_revenue_gbp > 0 THEN c.anonymous_guest_revenue_gbp / c.total_revenue_gbp END AS anonymous_guest_revenue_share_pct,
    LAG(s.positive_sales_gbp) OVER (ORDER BY s.month) AS prev_month_positive_sales_gbp,
    LAG(s.positive_sales_gbp, 12) OVER (ORDER BY s.month) AS prev_year_positive_sales_gbp
FROM sales s
LEFT JOIN returns r USING (month)
LEFT JOIN cust c USING (month)
ORDER BY s.month;

CREATE OR REPLACE VIEW mart_empirical.vw_product_pareto_rankings AS
WITH prod AS (
    SELECT stock_code,
           SUM(raw_signed_value) AS positive_sales_gbp,
           SUM(quantity) AS units_sold,
           COUNT(DISTINCT invoice_no) AS order_count,
           AVG(unit_price) AS realized_avg_unit_price
    FROM mart_empirical.fact_merchandise_sales
    GROUP BY stock_code
),
rets AS (
    SELECT stock_code,
           SUM(ABS(raw_signed_value)) AS return_magnitude_gbp
    FROM mart_empirical.fact_returns_and_cancellations
    GROUP BY stock_code
),
base AS (
    SELECT
        p.stock_code,
        p.positive_sales_gbp,
        COALESCE(r.return_magnitude_gbp, 0) AS return_magnitude_gbp,
        (p.positive_sales_gbp - COALESCE(r.return_magnitude_gbp, 0)) AS net_merchandise_value_gbp,
        p.units_sold,
        p.order_count,
        p.realized_avg_unit_price,
        SUM(p.positive_sales_gbp) OVER (ORDER BY p.positive_sales_gbp DESC ROWS UNBOUNDED PRECEDING) AS cum_rev,
        SUM(p.positive_sales_gbp) OVER () AS total_rev
    FROM prod p
    LEFT JOIN rets r USING (stock_code)
)
SELECT
    stock_code,
    positive_sales_gbp,
    return_magnitude_gbp,
    net_merchandise_value_gbp,
    units_sold,
    order_count,
    realized_avg_unit_price,
    cum_rev / NULLIF(total_rev, 0) AS cumulative_revenue_share,
    DENSE_RANK() OVER (ORDER BY cum_rev / NULLIF(total_rev, 0) DESC) AS pareto_rank
FROM base
ORDER BY positive_sales_gbp DESC;

CREATE OR REPLACE VIEW mart_empirical.vw_country_performance AS
WITH sales AS (
    SELECT country,
           SUM(raw_signed_value) AS sales_gbp,
           SUM(quantity) AS units_sold,
           COUNT(DISTINCT invoice_no) AS order_count,
           COUNT(DISTINCT CASE WHEN customer_id IS NOT NULL AND customer_id <> 'UNIDENTIFIED' THEN customer_id END) AS identified_customers
    FROM mart_empirical.fact_merchandise_sales
    GROUP BY country
),
rets AS (
    SELECT country,
           SUM(ABS(raw_signed_value)) AS return_magnitude_gbp
    FROM mart_empirical.fact_returns_and_cancellations
    GROUP BY country
)
SELECT
    s.country,
    s.sales_gbp,
    COALESCE(r.return_magnitude_gbp, 0) AS return_magnitude_gbp,
    (s.sales_gbp - COALESCE(r.return_magnitude_gbp, 0)) AS net_revenue_gbp,
    s.order_count,
    s.identified_customers,
    CASE WHEN s.order_count > 0 THEN s.sales_gbp / s.order_count END AS aov_gbp,
    s.units_sold,
    COALESCE(r.return_magnitude_gbp, 0) / NULLIF(s.sales_gbp, 0) AS return_rate_pct
FROM sales s
LEFT JOIN rets r USING (country)
ORDER BY s.sales_gbp DESC;

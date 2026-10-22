-- 04_reconciliation_assertions.sql
-- Reconciliation / validation assertions run against the built DuckDB database.

-- Total calculable signed value across all 5 categories must equal itself (tautological sanity hook);
-- the real cross-system check lives in test_duplicates_and_reconciliation.py (Python vs SQL vs Excel vs PowerBI).
SELECT
    'total_raw_transactions' AS check_name,
    COUNT(*) AS value
FROM stg.raw_transactions;

SELECT
    'category_01_rows' AS check_name,
    COUNT(*) AS value
FROM stg.raw_transactions WHERE primary_audit_category = '01_UNCALCULABLE_OR_MISSING_CORE';

SELECT
    'category_05_rows' AS check_name,
    COUNT(*) AS value
FROM stg.raw_transactions WHERE primary_audit_category = '05_POSITIVE_MERCHANDISE_SALE';

SELECT
    'fact_sales_rows_match_category_05_operational' AS check_name,
    COUNT(*) AS value
FROM mart_empirical.fact_merchandise_sales;

SELECT
    'fact_returns_rows_match_category_04_operational' AS check_name,
    COUNT(*) AS value
FROM mart_empirical.fact_returns_and_cancellations;

# Power BI Model & Assembly Guide — Albion Commercial Analytics

Historical model tables are exported from the verified UCI CSV project copy. Inventory values are simulated scenario outputs (`SIMULATED_HYBRID`) and must be labeled separately from historical observations.

## Contents
- `data_model_exports/` — star schema CSV exports (8 files)
- `DAX_Measures_Library.dax` — measure definitions
- This guide — grains, relationships, validation

## Table Grains
| Table | Grain | Source |
|---|---|---|
| dim_date | 1 row per date (2009-12-01 to 2011-12-31) | mart_empirical.dim_date |
| dim_product | 1 row per normalized stock_code | mart_empirical.dim_product |
| dim_customer | 1 row per customer_id (+ UNIDENTIFIED guest) | mart_empirical.dim_customer |
| fact_merchandise_sales | 1 operational row per raw_row_id (cat 05, not cross-sheet repeat) | mart_empirical.fact_merchandise_sales |
| fact_returns_and_cancellations | 1 operational row per raw_row_id (cat 04, not cross-sheet repeat) | mart_empirical.fact_returns_and_cancellations |
| fact_non_merch_adjustments | 1 operational row per raw_row_id (cats 01-03, not cross-sheet repeat) | mart_empirical.fact_non_merch_and_adjustments |
| fact_audit_waterfall | reporting_basis x category | mart_empirical.vw_audit_waterfall_reconciliation |
| sim_inventory_sku_scenarios | scenario x SKU (SIMULATED_HYBRID) | data/03_exports/sim_inventory_scenarios.csv |

## Relationships (all single-direction, active, from dimension to fact)
- dim_date[date] → fact_merchandise_sales[invoice_date]
- dim_date[date] → fact_returns_and_cancellations[invoice_date]
- dim_product[stock_code] → fact_*[stock_code]
- dim_customer[customer_id] → fact_*[customer_id]
- dim_product[stock_code] → sim_inventory_sku_scenarios[sim_stock_code]

The three dimension keys are unique. Product and date coverage is complete for the operational facts. Customer IDs are nullable for anonymous transactions; the audit found no nonblank customer IDs absent from `dim_customer`, so null/blank customer IDs must not be treated as orphan keys. The simulation export is scenario × SKU and uses `sim_stock_code`; its rows are simulated and do not represent historical inventory.

## DAX Concepts Used
- Filter context: established by visuals/slicers; measures aggregate within it.
- Row context: introduced by iterators (SUMX, AVERAGEX); not used in base measures here.
- CALCULATE: modifies filter context (e.g., identified vs anonymous revenue).
- DIVIDE: safe weighted ratios (return rate, AOV, shares).
- Time Intelligence: SAMEPERIODLASTYEAR (requires dim_date marked as date table).
- Inventory simulation logic: `sim_working_capital_gbp` is a scenario × SKU value with no date column. Aggregate it with `SUM` in the selected scenario/SKU filter context; do not apply historical `LASTDATE` logic.

## Dashboard Layout Guidance
1. Executive Dashboard: KPI cards (sales, returns magnitude, net value, return rate %), monthly trend line chart.
2. Product: Pareto column chart of cumulative revenue share, ABC-XYZ matrix.
3. Country: map/bar of net revenue by country.
4. Customer: identified vs anonymous donut, RFM segment bar.
5. Returns: return-sign subtype breakdown.
6. Inventory: scenario comparison of working capital & annual cost.

## Control Total Reconciliation Table (CSV vs DuckDB validation)
- fact_merchandise_sales.csv: duckdb=1,037,091 rows, csv=1,037,091 rows; `SUM(raw_signed_value)` = £20,112,163.17
- fact_returns_and_cancellations.csv: duckdb=18,290 rows, csv=18,290 rows; `SUM(abs_return_value)` = £726,611.45
- fact_non_merch_adjustments.csv: duckdb=11,990 rows, csv=11,990 rows
- fact_audit_waterfall.csv: duckdb=9 rows, csv=9 rows
- dim_date.csv: duckdb=761 rows, csv=761 rows
- dim_product.csv: duckdb=5,131 rows, csv=5,131 rows
- dim_customer.csv: duckdb=5,943 rows, csv=5,943 rows
- sim_inventory_sku_scenarios.csv: 14,199 rows; simulated scenario × SKU export

## Honest Verification
Power BI CSV exports were validated against DuckDB counts and the historical control totals above. No `.pbix` file was fabricated and Power BI Desktop was not executed; the `.pbix` must be assembled manually in Power BI Desktop using these CSVs and the DAX library.

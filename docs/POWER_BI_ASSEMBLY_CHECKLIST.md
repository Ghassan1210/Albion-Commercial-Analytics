# Power BI Assembly Checklist — Albion Commercial Analytics

**Purpose:** Manual, step-by-step instructions to assemble the Power BI report from the existing CSV exports. The historical sales, returns, customer, product, date, and audit tables are based on the verified UCI CSV copy; inventory tables are simulated scenarios. Power BI Desktop is NOT installed in this environment, so no `.pbix` file has been created.

**Source data:** `deliverables/powerbi/data_model_exports/` (8 CSVs). Historical tables use the verified UCI project copy (`data/01_raw/source/online_retail_ii_uci.csv`, SHA-256 `32569a66f3842a82b0d8c4d63b263c5d98a76bde5d1f65c6c01bf457e541d3a9`); `sim_inventory_sku_scenarios.csv` is explicitly simulated and must be labeled **[SIMULATED]**.

**Prerequisite:** Power BI Desktop (free from Microsoft) installed on your machine.

---

## Phase 1 — Import the 8 CSV exports

In Power BI Desktop: **Get Data → Text/CSV**, import each file from `deliverables/powerbi/data_model_exports/`. Load all 8 into the model. Use exact column names below.

| File | Key columns | Row count |
|------|-------------|---------------------|
| `dim_date.csv` | `date`, `year_month`, `year`, `quarter`, `month`, `day_name`, `is_weekend` | 761 |
| `dim_product.csv` | `stock_code`, `canonical_description`, `distinct_description_count`, `is_merchandise`, `first_sale_date`, `last_sale_date`, `median_unit_price` | 5,131 |
| `dim_customer.csv` | `customer_id`, `customer_status`, `primary_country`, `first_order_date`, `last_order_date` | 5,943 |
| `fact_merchandise_sales.csv` | `raw_row_id`, `source_sheet`, `invoice_no`, `stock_code`, `Description`, `quantity`, `invoice_date`, `unit_price`, `raw_signed_value`, `customer_id`, `country` | 1,037,091 |
| `fact_returns_and_cancellations.csv` | `raw_row_id`, `source_sheet`, `invoice_no`, `stock_code`, `Description`, `quantity`, `invoice_date`, `unit_price`, `raw_signed_value`, `return_sign_subtype`, `abs_return_value`, `customer_id`, `country` | 18,290 |
| `fact_non_merch_adjustments.csv` | `raw_row_id`, `source_sheet`, `invoice_no`, `stock_code`, `Description`, `quantity`, `invoice_date`, `unit_price`, `raw_signed_value`, `primary_audit_category`, `return_sign_subtype`, `customer_id`, `country` | 11,990 |
| `fact_audit_waterfall.csv` | `reporting_basis`, `primary_audit_category`, `total_rows`, `calculable_rows`, `uncalculable_rows`, `calculable_signed_gbp` | 9 |
| `sim_inventory_sku_scenarios.csv` | `data_provenance`, `scenario`, `sim_stock_code`, `sim_abc_class`, `sim_xyz_class`, `sim_sb_regime`, `sim_normal_approx_valid`, `sim_weekly_mean_units`, `sim_weekly_std_units`, `sim_cv`, `sim_adi`, `sim_annual_demand_units`, `sim_lead_time_mean_days`, `sim_lead_time_std_days`, `sim_lead_time_mean_weeks`, `sim_lead_time_std_weeks`, `sim_service_level`, `sim_z_score`, `sim_unit_cost_ratio`, `sim_unit_cost_gbp`, `sim_safety_stock_units`, `sim_safety_stock_normal_approx_units`, `sim_empirical_lt_demand_buffer_units`, `sim_reorder_point_units`, `sim_eoq_units`, `sim_cycle_stock_units`, `sim_working_capital_gbp`, `sim_annual_holding_cost_gbp`, `sim_annual_ordering_cost_gbp`, `sim_annual_inventory_cost_gbp`, `sim_carrying_cost_rate` | 14,199 |

> Confirm row counts match the table above. If any count differs, do not proceed — re-export from DuckDB.

---

## Phase 2 — Mark the date table

1. In Power BI Desktop, select `dim_date`.
2. **Table tools → Mark as date table** → Date column: `date`.
3. This is required for Time Intelligence (`SAMEPERIODLASTYEAR`) in the DAX measures.

---

## Phase 3 — Create relationships (single-direction, dimension → fact)

Dimension keys are unique and product/date coverage is complete for the operational facts. Customer IDs may be null/blank for anonymous transactions; these are not orphan keys. The audit found no nonblank customer IDs missing from `dim_customer`. The simulation product key coverage is complete (14,199 rows, 4,733 distinct `sim_stock_code` values, zero unmatched product keys).

**Manage relationships → New.** Create each relationship exactly once. Do NOT create bidirectional relationships.

| From (dimension) | To (fact) | Cardinality | Cross filter |
|------------------|-----------|-------------|--------------|
| `dim_date[date]` | `fact_merchandise_sales[invoice_date]` | One to Many | Single |
| `dim_date[date]` | `fact_returns_and_cancellations[invoice_date]` | One to Many | Single |
| `dim_product[stock_code]` | `fact_merchandise_sales[stock_code]` | One to Many | Single |
| `dim_product[stock_code]` | `fact_returns_and_cancellations[stock_code]` | One to Many | Single |
| `dim_product[stock_code]` | `fact_non_merch_adjustments[stock_code]` | One to Many | Single |
| `dim_customer[customer_id]` | `fact_merchandise_sales[customer_id]` | One to Many | Single |
| `dim_customer[customer_id]` | `fact_returns_and_cancellations[customer_id]` | One to Many | Single |
| `dim_customer[customer_id]` | `fact_non_merch_adjustments[customer_id]` | One to Many | Single |
| `dim_product[stock_code]` | `sim_inventory_sku_scenarios[sim_stock_code]` | One to Many | Single |

**Do not** create relationships directly between fact tables. Do not activate multiple relationships between the same pair of tables.

---

## Phase 4 — Create the DAX measures

Copy every measure from `deliverables/powerbi/DAX_Measures_Library.dax` into Power BI Desktop (**Table tools → New measure**). The full measure list:

| Measure | DAX expression |
|---------|----------------|
| Positive Merchandise Sales GBP | `SUM(fact_merchandise_sales[raw_signed_value])` |
| Cat04 Signed Returns GBP | `SUM(fact_returns_and_cancellations[raw_signed_value])` |
| Recorded Returns Magnitude GBP | `SUM(fact_returns_and_cancellations[abs_return_value])` |
| Net Recorded Merchandise Value GBP | `[Positive Merchandise Sales GBP] + [Cat04 Signed Returns GBP]` |
| Merchandise Return Rate % | `DIVIDE([Recorded Returns Magnitude GBP], [Positive Merchandise Sales GBP], 0)` |
| Net Cancellation Impact % | `DIVIDE(-[Cat04 Signed Returns GBP], [Positive Merchandise Sales GBP], 0)` |
| Identified Customer Revenue GBP | `CALCULATE([Positive Merchandise Sales GBP], fact_merchandise_sales[customer_id] <> "UNIDENTIFIED" && NOT ISBLANK(fact_merchandise_sales[customer_id]))` |
| Anonymous Guest Revenue GBP | `CALCULATE([Positive Merchandise Sales GBP], fact_merchandise_sales[customer_id] = "UNIDENTIFIED")` |
| Average Order Value GBP | `DIVIDE([Positive Merchandise Sales GBP], DISTINCTCOUNT(fact_merchandise_sales[invoice_no]), 0)` |
| Sales LY | `CALCULATE([Positive Merchandise Sales GBP], SAMEPERIODLASTYEAR(dim_date[date]))` |
| YoY Sales % | `DIVIDE([Positive Merchandise Sales GBP] - [Sales LY], [Sales LY], 0)` |
| Sim Working Capital GBP | `SUM(sim_inventory_sku_scenarios[sim_working_capital_gbp])` within the selected scenario/SKU context; simulated scenario value, not historical inventory |

Copy the DAX exactly as written in `DAX_Measures_Library.dax`. Do not invent additional measures.

---

## Phase 5 — Build the report pages

Create one report page per dashboard area. Label historical UCI-derived visuals **[HISTORICAL UCI]** and inventory-scenario visuals **[SIMULATED]**.

| Page | Visuals | Measures / fields |
|------|---------|-------------------|
| Executive Overview | KPI cards: Positive Merchandise Sales GBP, Recorded Returns Magnitude GBP, Net Recorded Merchandise Value GBP, Merchandise Return Rate %, Identified Customer Revenue GBP, Anonymous Guest Revenue GBP, Average Order Value GBP | DAX measures; `dim_date` slicer |
| Monthly Trends | Line chart: Positive Merchandise Sales GBP over `dim_date[date]` | DAX measure + `dim_date[date]` |
| Product Analysis | Column chart: Positive Merchandise Sales GBP by `dim_product[stock_code]`; cumulative revenue share | DAX measure + `dim_product[stock_code]` |
| Country Analysis | Bar/map: Net Recorded Merchandise Value GBP by `dim_customer[primary_country]` | DAX measure + `dim_customer[primary_country]` |
| Customer Analysis | Donut: Identified vs Anonymous Guest Revenue GBP; bar: `dim_customer[customer_status]` | DAX measures + `dim_customer[customer_status]` |
| Returns & Adjustments | Bar chart: Cat04 Signed Returns GBP / Recorded Returns Magnitude GBP by `fact_returns_and_cancellations[return_sign_subtype]` | DAX measures + `fact_returns_and_cancellations[return_sign_subtype]` |
| Inventory Scenarios | Table/matrix: `sim_working_capital_gbp`, `sim_annual_inventory_cost_gbp`, `sim_eoq_units`, `sim_safety_stock_units` by `sim_inventory_sku_scenarios[scenario]` | DAX measure + `sim_inventory_sku_scenarios[scenario]` |

---

## Phase 6 — Validate control totals against DuckDB

Compare each fact export's row count and key totals in Power BI against the DuckDB `database/albion_analytics.duckdb` values:

| Export | DuckDB rows | Power BI row count | Key total to match |
|--------|-------------|--------------------|--------------------|
| `fact_merchandise_sales.csv` | 1,037,091 | must equal 1,037,091 | `SUM(raw_signed_value)` = £20,112,163.17 |
| `fact_returns_and_cancellations.csv` | 18,290 | must equal 18,290 | `SUM(abs_return_value)` = £726,611.45 |
| `fact_non_merch_adjustments.csv` | 11,990 | must equal 11,990 | — |
| `dim_product.csv` | 5,131 | must equal 5,131 | — |
| `dim_customer.csv` | 5,943 | must equal 5,943 | — |

If any Power BI total differs from DuckDB, re-check relationships and filters before publishing.

---

## Phase 7 — Save the .pbix

Save the completed report as:

`deliverables/powerbi/Albion_Commercial_Analytics.pbix`

**Do not** save under any other name. Historical pages must be labeled **[HISTORICAL UCI]** and inventory pages/measures **[SIMULATED]**.

---

## Current status

| Item | Status |
|------|--------|
| 8 CSV exports | Present and validated against DuckDB |
| DAX measures library | Present (`DAX_Measures_Library.dax`) |
| Assembly guide | Present (`PowerBI_Model_and_Assembly_Guide.md`) |
| Power BI Desktop installed | NO |
| `.pbix` file created | NO |
| `.pbix` location (when created) | `deliverables/powerbi/Albion_Commercial_Analytics.pbix` |

**Blocker:** Power BI Desktop is not installed in this environment. The `.pbix` cannot be created here. A person with Power BI Desktop access must perform Phases 1–7 manually using this checklist.

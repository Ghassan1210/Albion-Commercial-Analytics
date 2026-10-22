# Albion Commercial Analytics — Project Master Guide

This guide explains what the project does, where its outputs live, how the pieces fit together, and how to operate it safely.

## 1. Executive explanation

Albion Commercial Analytics turns the historical UCI Online Retail II transaction ledger into a controlled commercial-analysis package. The project separates positive merchandise sales, returns and cancellations, non-merchandise adjustments, customer and product dimensions, reconciliation controls, and clearly labelled simulated inventory scenarios. It delivers a reproducible DuckDB analytical database, an Excel workbook, an editable Power BI project, a saved PBIX report, tests, and documentation.

Albion is a fictional analytical wrapper. The source records are not transactions from a real company called Albion and are not a live business feed.

## 2. Dataset provenance and limitations

The source is Chen, D. (2012), *Online Retail II*, UCI Machine Learning Repository, DOI `10.24432/C5CG6D`, licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The supplied source CSV is `data\01_raw\source\online_retail_ii_uci.csv`, covering historical transactions from December 2009 through December 2011. Its source row count is 1,067,371.

Customer IDs are blank for anonymous transactions. The current operational facts contain 234,447 blank merchandise customer IDs, 353 blank return/cancellation IDs, and 8,207 blank non-merchandise IDs. These rows are retained as anonymous activity. The dataset has ordinary retail-ledger limitations: cancellations and returns need classification, descriptions vary, and customer coverage is not complete for every transaction.

## 3. Folder map

| Location | Purpose |
|---|---|
| `data\01_raw\source` | Genuine source CSV |
| `data\04_reconciliation` | Reconciliation outputs and validation report |
| `database\albion_analytics.duckdb` | Analytical DuckDB database |
| `src\ingestion` | Source acquisition and ingestion |
| `src\transformation` | Classification, diagnostics and star-schema building |
| `src\analytics` | Commercial, customer, product, price and seasonal analytics |
| `src\simulation` | Inventory and working-capital scenarios |
| `src\reporting` | Notebook, Excel, Power BI and documentation builders |
| `sql` | DDL, transformations, analytical views and validation assertions |
| `deliverables\excel\Albion_Commercial_Analytics.xlsx` | Analyst workbook |
| `deliverables\powerbi\data_model_exports` | Eight CSV inputs for Power BI |
| `deliverables\powerbi\Albion_Commercial_Analytics_Project` | Editable PBIP source |
| `deliverables\powerbi\Albion_Commercial_Analytics.pbix` | Saved Power BI report |
| `deliverables\powerbi\DAX_Measures_Library.dax` | Approved DAX definitions |
| `docs` | Methodology, validation and operating documentation |
| `tests` | Pytest suite |
| `notebooks` | Executed analytical notebook |
| `scripts\refresh_analytics.ps1` | Controlled manual refresh helper |

## 4. Architecture and data flow

1. **Ingestion:** the source file is checked and loaded by `src\ingestion`.
2. **Staging and classification:** Python and SQL standardise dates, IDs, descriptions, quantities and prices, then classify rows into merchandise sales, returns/cancellations and non-merchandise adjustments.
3. **Analytical storage:** SQL creates the star-schema tables in DuckDB.
4. **Analytics:** Python modules calculate commercial metrics, customer intelligence, product demand analysis and seasonal outputs.
5. **Reconciliation:** category-level counts and signed values are compared to the raw ledger.
6. **Outputs:** reporting modules write the Excel workbook, Power BI CSV package, notebook and documentation.
7. **Power BI:** Power Query reads the eight CSV exports; TMDL defines tables and relationships; DAX defines measures; PBIR defines report pages and visuals.

## 5. Tool roles

- **Python/pandas:** ingestion, typed transformations and analytical calculations.
- **SQL/DuckDB:** durable analytical tables, views and assertions in a local columnar database.
- **Excel:** compact workbook for analyst review and sharing.
- **Power Query/M:** typed CSV connections inside the Power BI semantic model.
- **DAX:** measures evaluated in filter context, such as sales and return rates.
- **Power BI:** interactive report pages, relationships, slicers and management visuals.
- **Jupyter:** reproducible exploratory and explanatory notebook output.
- **pytest:** regression tests for transformations, controls and edge cases.
- **Git/GitHub:** version control and public sharing of editable source and documentation; raw data, databases, backups and local state are excluded.
- **VS Code:** project editing, terminal work and review.
- **AI coding assistants:** assisted with implementation and review; all claims in this guide are based on the files and checks recorded in the project.

## 6. Data model

### Dimensions

- `dim_date`: one row per calendar date; key `date`.
- `dim_product`: one row per `stock_code`; canonical description and product-date/price attributes.
- `dim_customer`: one row per `customer_id`; customer status, primary country and order dates.

### Facts and supporting tables

- `fact_merchandise_sales`: one source-ledger row per `raw_row_id` for positive merchandise sales.
- `fact_returns_and_cancellations`: one source-ledger row per `raw_row_id` for merchandise cancellations or returns.
- `fact_non_merch_adjustments`: one source-ledger row per `raw_row_id` for fees, charges and zero/negative-price adjustments.
- `fact_audit_waterfall`: aggregated reconciliation rows by reporting basis and audit category.
- `sim_inventory_sku_scenarios`: SKU × scenario rows for configured inventory simulations; not historical inventory.

### Nine intended relationships

All are active, one-to-many, single-direction relationships from dimensions to facts:

1. `dim_date[date]` → `fact_merchandise_sales[invoice_date]`
2. `dim_date[date]` → `fact_returns_and_cancellations[invoice_date]`
3. `dim_product[stock_code]` → `fact_merchandise_sales[stock_code]`
4. `dim_product[stock_code]` → `fact_returns_and_cancellations[stock_code]`
5. `dim_product[stock_code]` → `fact_non_merch_adjustments[stock_code]`
6. `dim_customer[customer_id]` → `fact_merchandise_sales[customer_id]`
7. `dim_customer[customer_id]` → `fact_returns_and_cancellations[customer_id]`
8. `dim_customer[customer_id]` → `fact_non_merch_adjustments[customer_id]`
9. `dim_product[stock_code]` → `sim_inventory_sku_scenarios[sim_stock_code]`

No historical date relationship is created for the simulation table.

### Approved measures

The twelve measures in `DAX_Measures_Library.dax` are: `Positive Merchandise Sales GBP`, `Identified Customer Revenue GBP`, `Anonymous Guest Revenue GBP`, `Average Order Value GBP`, `Sales LY`, `YoY Sales %`, `Cat04 Signed Returns GBP`, `Recorded Returns Magnitude GBP`, `Net Recorded Merchandise Value GBP`, `Merchandise Return Rate %`, `Net Cancellation Impact %`, and `Sim Working Capital GBP`.

## 7. Business definitions and controls

- **Positive merchandise sales:** the signed value of rows classified as positive merchandise sales.
- **Signed returns/cancellations:** the signed `raw_signed_value` of the return/cancellation fact, normally negative.
- **Absolute return magnitude:** `abs_return_value`, useful for reporting the scale of returned or cancelled value without sign.
- **Merchandise return rate:** absolute return magnitude divided by positive merchandise sales.
- **Customer coverage:** identified versus anonymous activity based on the customer ID field; blank IDs remain anonymous.
- **Net recorded merchandise value:** positive merchandise sales plus signed return/cancellation value.

Do not add separate fact totals in a way that double-counts the same ledger basis. Use the merchandise fact for sales, the returns fact for return measures, and the non-merchandise fact for adjustments.

Verified controls:

- Merchandise rows: 1,037,091; signed value **£20,112,163.17**
- Returns/cancellations rows: 18,290; signed value **−£726,611.45**; absolute magnitude **£726,611.45**
- Net merchandise value: **£19,385,551.72**
- Net non-merchandise value: **−£98,301.17**
- Total calculable signed value: **£19,287,250.55**

## 8. Inventory simulations

The simulation is a configured scenario model at SKU × scenario grain. It uses demand history-derived features plus assumptions for service level, lead time, unit cost, carrying cost and ordering behaviour. Scenarios include a baseline, a lead-time shock and a cost-inflation case. Outputs include safety stock, reorder point, EOQ, working capital and annual inventory cost.

These are hypothetical planning scenarios. They are not historical inventory balances, actual company working capital, or live forecasts. Compare scenarios side by side; do not sum alternative scenarios into one historical KPI.

## 9. Excel operating guide

The verified workbook is [Albion_Commercial_Analytics.xlsx](../deliverables/excel/Albion_Commercial_Analytics.xlsx). Its sheets are:

- **Executive Dashboard:** compact headline view.
- **KPI Summary:** key commercial metrics.
- **Monthly Trends:** period-level trends.
- **Product Analysis:** product rankings and value/volume analysis.
- **Country Analysis:** country comparisons.
- **Customer Analysis:** customer coverage and customer-level summaries.
- **Returns & Adjustments:** return and adjustment analysis.
- **Data Quality:** validation and anomaly checks.
- **Inventory Scenarios:** simulated scenario outputs.
- **Data Dictionary:** field and definition reference.

## 10. Power BI operating guide

Open the editable project from `deliverables\powerbi\Albion_Commercial_Analytics_Project\Albion_Commercial_Analytics.pbip`. The saved PBIX is now verified at `deliverables\powerbi\Albion_Commercial_Analytics.pbix`.

The report contains five pages: Executive Overview, Sales Performance, Product & Customer Intelligence, Returns & Reconciliation, and Inventory Scenario Analysis. The PBIX archive contains 5/4/4/4/4 visual definitions. Inventory pages are explicitly simulated; historical sales and returns remain separate.

The Power Query definitions use the local folder `deliverables\powerbi\data_model_exports`. If the project is moved, update those source paths in Power BI Desktop. To refresh, open the PBIP/PBIX, choose **Refresh**, inspect any table errors, and verify the control totals. To create a PBIX from PBIP, use **File → Save As**, choose Power BI Desktop `.pbix`, and save to the canonical deliverables path. Do not rename the `.pbip` file.

If the incomplete-data banner appears, inspect the affected query in Power Query and capture its exact error. Do not delete rows or disable loading to hide it.

## 11. Reproducibility

From the project root:

```powershell
\.venv\Scripts\python.exe -m pytest tests -q
powershell -ExecutionPolicy Bypass -File .\scripts\refresh_analytics.ps1
```

The helper performs validation-only checks by default. It checks the Python environment, genuine source, eight exports and the reconciliation report. Use `-ExecutePipeline` only when deliberately regenerating outputs:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\refresh_analytics.ps1 -ExecutePipeline
```

The pipeline entry point is `run_pipeline.py`; it stops on a failed milestone and does not pretend that downstream outputs succeeded.

## 12. Quality assurance

The current focused pytest run passed 31 tests. The eight export row counts are 761, 5,131, 5,943, 1,037,091, 18,290, 11,990, 9 and 14,199 respectively. Dimension keys are unique, simulation product keys are covered, and blank customer IDs are retained as anonymous activity.

The validation JSON remains stale relative to the current genuine outputs and should be regenerated through the normal pipeline rather than hand-edited. Desktop rendering and the earlier incomplete-data warning require direct Desktop observation.

## 13. GitHub workflow

The public repository is [Albion-Commercial-Analytics](https://github.com/Ghassan1210/Albion-Commercial-Analytics). Review changes with `git status`, `git diff`, and `git diff --cached`. Stage only source, documentation and approved PBIP definitions. Keep raw data, DuckDB, generated exports, backups, `.pbi` state, credentials and unrelated files excluded. Commit on `main`, push with `git push origin main`, and verify with `git ls-remote --heads origin`.

## 14. Manager/interviewer explanation

This is a controlled retail analytics case study that turns a large historical transaction ledger into a star-schema model with reconciliation controls and an interactive Power BI report. The project demonstrates practical classification, dimensional modelling, financial control totals, customer coverage handling, scenario analysis and reproducible delivery. Python and SQL perform the repeatable data work; DuckDB provides local analytical storage; Excel supports analyst review; Power BI provides management-facing exploration.

Typical questions and accurate answers:

- **Why separate facts?** Sales, returns and adjustments have different business meanings and must not be double-counted.
- **Are inventory figures actual?** No. They are simulated scenarios based on configured assumptions.
- **Why are customer totals incomplete?** The source contains blank customer IDs; those transactions are retained as anonymous.
- **How is quality demonstrated?** Row counts, dimension-key checks, reconciliation categories, signed controls and automated tests.
- **What would you improve next?** Make Power Query paths portable, regenerate the validation JSON as part of the controlled refresh, and capture a repeatable Desktop refresh validation.

## 15. Next improvements

1. Capture and document a successful Desktop refresh with the incomplete-data warning resolved or explained.
2. Replace machine-specific Power Query paths with a safe parameter or documented deployment setting.
3. Regenerate the stale validation JSON through the normal pipeline.
4. Keep the PBIP source and PBIX delivery clearly separated in release documentation.

# Albion Commercial Analytics — Final Delivery and Data Audit

**Audit date:** 2026-10-22
**Project root:** `C:\Important GHN files\GHN12`

## Executive summary

The genuine UCI Online Retail II CSV is present and its SHA-256 is `32569a66f3842a82b0d8c4d63b263c5d98a76bde5d1f65c6c01bf457e541d3a9`. The eight Power BI exports are present at `deliverables\powerbi\data_model_exports` with the expected row counts. Read-only reconciliation reproduces the documented merchandise, returns, non-merchandise, net merchandise and total signed-value controls exactly. The focused test suite passes 31 tests.

The editable PBIP source is available at `deliverables\powerbi\Albion_Commercial_Analytics_Project\Albion_Commercial_Analytics.pbip`; 34 JSON definitions parse and the model contains eight business tables, the nine intended business relationships, and twelve measures. The canonical PBIX is **not present**. Power BI Desktop previously displayed all eight expected table row counts but also showed the generic incomplete/no-data warning; that warning remains unverified as fully resolved. The next required action is to open the PBIP in Desktop, investigate/refresh the warning, and use **File → Save As** to create `deliverables\powerbi\Albion_Commercial_Analytics.pbix`.

## Provenance and limitations

The source is Chen, D. (2012), *Online Retail II*, UCI Machine Learning Repository, DOI `10.24432/C5CG6D`, licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). It covers historical transactions from December 2009 through December 2011; it is not a live Albion feed. Customer IDs are blank for anonymous transactions. Product and customer dimensions are analytical dimensions derived from the ledger. Inventory outputs are simulated SKU scenarios and must not be presented as historical stock or actual company working capital.

The existing `data\04_reconciliation\final_validation_report.json` is stale and internally contradictory: it contains fixture-scale reconciliation values, says the UCI XLSX is unavailable, and reports fixture-mode evidence while also identifying the genuine CSV. It was not edited. The supported regeneration mechanism is the existing full `run_pipeline.py` workflow, which was not run during this audit.

## Architecture and data flow

The raw CSV is ingested by `run_pipeline.py` and the Python/SQL modules under `src` and `sql`. DuckDB stores analytical tables in `database\albion_analytics.duckdb`. The pipeline writes the Excel workbook and eight Power BI CSV exports. Power BI Power Query reads those CSVs, TMDL defines the semantic model and relationships, and DAX supplies the twelve approved measures. Tests validate transformations and controls. Git tracks the editable source project and documentation; the public repository is `https://github.com/Ghassan1210/Albion-Commercial-Analytics`.

## Verified deliverables

| Asset | Current evidence |
|---|---|
| Raw source | `data\01_raw\source\online_retail_ii_uci.csv`, 94,850,204 bytes; SHA-256 above |
| DuckDB | `database\albion_analytics.duckdb`, 314,322,944 bytes |
| Excel | `deliverables\excel\Albion_Commercial_Analytics.xlsx`, 22,917 bytes; readable with 10 sheets |
| PBIP | `deliverables\powerbi\Albion_Commercial_Analytics_Project\Albion_Commercial_Analytics.pbip`, present |
| PBIX | `deliverables\powerbi\Albion_Commercial_Analytics.pbix`, **missing** |
| Validation JSON | `data\04_reconciliation\final_validation_report.json`, present but stale/contradictory |
| Refresh helper | `scripts\refresh_analytics.ps1`, syntax-valid; validation-only execution fails honestly because the stale JSON lacks current controls |

Excel sheets and dimensions: Executive Dashboard (5×2), KPI Summary (8×2), Monthly Trends (27×13), Product Analysis (52×9), Country Analysis (45×9), Customer Analysis (4×5), Returns & Adjustments (3×4), Data Quality (11×6), Inventory Scenarios (5×6), Data Dictionary (9×3).

## Tables, grains and controls

| Export | Rows | Grain / key evidence |
|---|---:|---|
| `dim_date.csv` | 761 | one row per date; `date` unique; 2009-12-01 to 2011-12-31 |
| `dim_product.csv` | 5,131 | one row per `stock_code`; key unique |
| `dim_customer.csv` | 5,943 | one row per `customer_id`; key unique |
| `fact_merchandise_sales.csv` | 1,037,091 | one ledger row per `raw_row_id`; key unique |
| `fact_returns_and_cancellations.csv` | 18,290 | one return/cancellation ledger row per `raw_row_id`; key unique |
| `fact_non_merch_adjustments.csv` | 11,990 | one non-merchandise adjustment row per `raw_row_id`; key unique |
| `fact_audit_waterfall.csv` | 9 | aggregated audit-category control rows |
| `sim_inventory_sku_scenarios.csv` | 14,199 | SKU × scenario rows; all `sim_stock_code` values covered by `dim_product` |

The three operational facts contain blank customer IDs for anonymous rows: merchandise 234,447; returns/cancellations 353; non-merchandise 8,207. After treating those as anonymous, each fact has zero nonblank customer IDs missing from `dim_customer`. Date and product relationship coverage is complete for the documented keys.

Financial controls recomputed from the exports:

- Positive merchandise sales: **£20,112,163.17**
- Signed returns/cancellations: **−£726,611.45**
- Absolute returns/cancellations: **£726,611.45**
- Net merchandise value: **£19,385,551.72**
- Net non-merchandise value: **−£98,301.17**
- Total calculable signed value: **£19,287,250.55**

These values are calculated across separate facts and must not be double-counted in a single visual. The audit waterfall export contains the same current signed controls.

## Power BI status

The source project is at `deliverables\powerbi\Albion_Commercial_Analytics_Project`. Static checks found 34 syntactically valid JSON files, eight business tables, twelve measures, and the nine intended single-direction dimension-to-fact relationships; Desktop-generated local date tables/relationships may also be present. Power Query expressions point to the local `deliverables\powerbi\data_model_exports` folder and the repaired fact-date conversion handles timestamp text safely.

The five planned report pages are Executive Overview, Sales Performance, Product & Customer Intelligence, Returns & Reconciliation, and Inventory Scenario Analysis. The project remains machine-path dependent. Desktop previously showed the eight expected row counts, but the generic “Some of the tables have incomplete or no data” banner was also observed, so a fully successful refresh is **not** claimed. The PBIX has not been verified on disk.

### Visual-definition update

The four non-executive page folders originally contained only `page.json` and no visual definitions. A backup was created at `deliverables\powerbi\Albion_Commercial_Analytics_Project_backup_before_visual_build` before the focused PBIR edit. The active project now contains 5 Executive Overview visuals and 4 visuals on each remaining page (30 report JSON files total, all syntactically valid):

- Sales Performance: sales total card, average-order-value card, monthly sales line chart, country sales bar chart.
- Product & Customer Intelligence: identified-revenue card, anonymous-revenue card, product sales bar chart, customer-country bar chart.
- Returns & Reconciliation: returns-magnitude card, return-rate card, monthly returns line chart, audit-waterfall table.
- Inventory Scenario Analysis: simulated working-capital card, scenario annual-cost chart, safety-stock chart, reorder-point chart.

The new visuals use only verified model fields and existing measures. Desktop rendering and filter interaction after this source edit remain **NOT VERIFIED**; the canonical PBIX is still missing.

## Reproducibility and refresh

Use the existing `.venv` and documented dependencies. Run focused tests with `python -m pytest tests -q`. Run `scripts\refresh_analytics.ps1` without `-ExecutePipeline` for validation-only checks. Use `-ExecutePipeline` only when intentionally regenerating outputs; it stops on a nonzero pipeline exit. After a successful regeneration, refresh the PBIP/PBIX in Power BI Desktop and recheck the controls above.

## Known issues and next priorities

1. Save and verify the canonical PBIX in `deliverables\powerbi\Albion_Commercial_Analytics.pbix`.
2. Investigate the Desktop incomplete/no-data warning despite observed row counts.
3. Regenerate `final_validation_report.json` through the normal pipeline rather than editing it manually.
4. Remove or archive the untracked duplicate `Albion_Commercial_Analytics1` PBIP created during Desktop work only after confirming it is not needed.
5. Replace remaining stale fixture wording in older status/tutorial documents during a separate documentation pass.

## Portfolio explanation

This project turns a historical retail ledger into a controlled commercial analytics model: Python and SQL classify transactions, DuckDB provides reproducible storage, Excel gives a compact analyst workbook, and Power BI provides an editable semantic model with DAX measures for sales, returns, reconciliation and clearly labelled simulated inventory scenarios. The strongest presentation point is the explicit reconciliation from source rows to signed commercial value, with anonymous customers and simulation assumptions kept visible rather than hidden.

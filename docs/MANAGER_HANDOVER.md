# Albion Commercial Analytics — Manager Handover

**Project root:** `C:\Important GHN files\GHN12`
**Prepared:** 2026-10-21
**Presented to:** Manager

---

## A. Project purpose

Albion Commercial Analytics demonstrates a structured commercial analytics workflow built with Python, SQL, DuckDB, Excel, and Power BI integration. It ingests transaction records, classifies them forensically (including returns, cancellations, and non-merchandise charges), builds a DuckDB star schema, computes commercial and customer KPIs, runs an inventory/working-capital simulation, and produces an Excel workbook, Power BI model exports, a Jupyter notebook, automated tests, and documentation.

"Albion" is a fictional case-study wrapper. The underlying transaction records are the UCI Machine Learning Repository **Online Retail II** dataset (Chen, D. 2012, CC BY 4.0). The data did **not** originate from a real company called Albion.

---

## B. What has been built

| Component | What it does | Status |
|-----------|--------------|--------|
| Python/SQL pipeline (`run_pipeline.py`) | End-to-end ingestion, classification, star-schema build, analytics, simulation, reporting | Built and runnable (exit code 0) |
| DuckDB database | Star schema: dimensions (date, product, customer) and facts (sales, returns, non-merchandise) plus 4 analytics views | Built; row counts stable on rerun |
| Analytics | Commercial KPIs, RFM/cohorts, ABC–XYZ demand regimes, observational price–quantity, seasonal forecast | Built; tested |
| Inventory simulation | SIMULATED_HYBRID working-capital across 3 scenarios (baseline, lead-time shock, cost inflation) | Built; configured assumptions, not empirical |
| Excel workbook | 10-sheet executive workbook with KPIs, trends, product/country/customer analysis, returns, data quality, inventory scenarios | Built; 10 sheets verified |
| Power BI package | 8 CSV star-schema exports, DAX measures library, model assembly guide | Built; no `.pbix`, Desktop not run |
| Jupyter notebook | Executed walkthrough of forensics, KPIs, duplication, returns, trends, ABC–XYZ, RFM, price–quantity, forecast, simulation | Built; 11 code cells with outputs, 0 errors |
| Automated tests | pytest suite covering ingestion, classification, duplicates, SQL, simulation, deliverables | Built; **31 passed, 0 failed** |
| Documentation | README, data dictionary, provenance, KPI definitions, methodology, executive summary, walkthrough, teacher demo script | Built; 8 files |

---

## C. What has been verified

- **Tests:** 31 passed, 0 failed (`pytest tests -v`, exit code 0).
- **Reconciliation:** 28 independent checks across Python, DuckDB SQL, JSON, Power BI CSV exports, and Excel workbook cells — 0 failures.
- **Idempotency:** Rerunning the pipeline does not duplicate rows or corrupt outputs (table counts stable: 805 raw / 105 sales / 15 returns).
- **Notebook:** All 11 code cells contain saved outputs; 0 error outputs.
- **Excel:** Opens programmatically; 10 sheets present; KPI cells reconcile with DuckDB.
- **Power BI exports:** CSV row counts match DuckDB; DAX and assembly guide present.

---

## D. Business value

The architecture demonstrates how to:
- Ingest and forensically classify commercial transactions (sales, returns/cancellations, fees, uncalculable records).
- Reconcile monetary values across classification categories with signed-return logic.
- Measure customer concentration (identified vs. anonymous-guest revenue), RFM segments, and cohorts.
- Rank products by Pareto revenue and classify demand (ABC–XYZ and Syntetos-Boylan regimes).
- Simulate inventory working capital under baseline, lead-time shock, and cost-inflation scenarios.
- Deliver results through Excel, Power BI-ready exports, and an executed notebook.

**Fixture vs. genuine data:** All current results are computed from an 805-row **synthetic test fixture**, not the full UCI dataset (1,067,371 rows). The pipeline and calculations are verified, but the numerical findings are **not** representative business conclusions from the full dataset. Full-data analysis requires the genuine UCI file.

---

## E. Important limitation

The real UCI Online Retail II dataset could not be downloaded during this project (network/firewall restriction). The current source at `data/01_raw/online_retail_II.xlsx` is an 805-row synthetic fixture (`fixture_mode: true` in `data/04_reconciliation/provenance_manifest.json`). Current results demonstrate the engineering workflow and are **not** production business findings from the full dataset. To run full-data analysis, place the unmodified `online_retail_II.xlsx` at `data/01_raw/source/online_retail_ii_uci.xlsx` and run `run_pipeline.py --mode full`.

---

## F. Demonstration sequence

1. **README and architecture** — `README.md` and `docs/PROJECT_STATUS_AND_ROADMAP.md`
2. **Excel workbook** — `deliverables/excel/Albion_Commercial_Analytics.xlsx` (10 sheets)
3. **Power BI package** — `deliverables/powerbi/data_model_exports/` (8 CSVs), `DAX_Measures_Library.dax`, `PowerBI_Model_and_Assembly_Guide.md`
4. **Python/SQL pipeline and DuckDB** — `src/`, `sql/`, `database/albion_analytics.duckdb`
5. **Automated test results** — run `.venv\Scripts\python -m pytest tests -v` (31 passed, 0 failed)
6. **Engineering report and limitations** — `docs/FINAL_ENGINEERING_REPORT.md`, `data/04_reconciliation/final_validation_report.json`

Commands are run from `C:\Important GHN files\GHN12` using `.venv\Scripts\python.exe`.

---

**Bottom line:** The engineering is complete, tested, and reconciled on the available fixture. The project is ready to demonstrate, with the fixture limitation disclosed. Full-data business conclusions await the genuine UCI dataset.

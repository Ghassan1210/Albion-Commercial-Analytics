# Albion Commercial Analytics — 5-Minute Demo Guide

**Project root:** `C:\Important GHN files\GHN12`
**Environment:** `.venv\Scripts\python.exe` (Python 3.13.15)
**Dataset basis:** 805-row synthetic fixture (`fixture_mode: true`) — NOT the full UCI dataset (1,067,371 rows). Full-data analysis is blocked until the genuine UCI workbook is obtained manually.

---

## 1. Project purpose & architecture (1 minute)

Albion Commercial Analytics demonstrates a structured commercial-transaction analytics workflow:
- **Python** ingestion & transformation (forensic classification of sales, returns/cancellations, fees, uncalculable records)
- **DuckDB + SQL** star schema (dimensions: date, product, customer; facts: sales, returns, non-merchandise; 4 analytics views)
- **Commercial & customer analytics** (KPIs, RFM/cohorts, ABC–XYZ demand regimes, price–quantity analysis, seasonal forecast)
- **Inventory/working-capital simulation** (SIMULATED_HYBRID — configured assumptions, not empirical)
- **Excel reporting** (10 sheets), **Power BI package** (8 CSV exports + DAX + assembly guide), **Jupyter notebook**, **automated tests**, **documentation**

**"Albion" is a fictional case-study wrapper.** The underlying transaction records are the UCI Machine Learning Repository Online Retail II dataset (Chen, D. 2012, CC BY 4.0). The data did not originate from a real company called Albion.

---

## 2. Run the pipeline & inspect DuckDB (1 minute)

From `C:\Important GHN files\GHN12`:

```powershell
# Verify the environment
.venv\Scripts\python.exe --version

# Run the fixture pipeline (exit code 0, idempotent)
.venv\Scripts\python.exe run_pipeline.py --mode fixture

# Inspect the DuckDB database
.venv\Scripts\python.exe -c "
import duckdb
con = duckdb.connect('database/albion_analytics.duckdb', read_only=True)
for t in ['stg.raw_transactions','core_empirical.classified_ledger','mart_empirical.fact_merchandise_sales','mart_empirical.fact_returns_and_cancellations','mart_empirical.fact_non_merch_and_adjustments']:
    print(t, con.execute('SELECT COUNT(*) FROM '+t).fetchone()[0])
con.close()
"
```

Expected table counts: raw_transactions 805, classified_ledger 805, fact_sales 105, fact_returns 15, fact_non_merch 685.

---

## 3. Excel workbook (1 minute)

`deliverables/excel/Albion_Commercial_Analytics.xlsx` — 10 sheets:
1. Executive Dashboard
2. KPI Summary
3. Monthly Trends
4. Product Analysis
5. Country Analysis
6. Customer Analysis
7. Returns & Adjustments
8. Data Quality
9. Inventory Scenarios
10. Data Dictionary

Open with Excel and review the KPI Summary and Data Quality sheets. Key KPIs (fixture-based): positive merchandise sales £56,078.93; return magnitude £2,912.00; net recorded merchandise value £56,818.37; return rate 5.19%; identified revenue £43,483.30 / anonymous £12,595.63.

---

## 4. Power BI package (30 seconds)

`deliverables/powerbi/`:
- `data_model_exports/` — 8 CSV star-schema exports (dim_date, dim_product, dim_customer, fact_merchandise_sales, fact_returns_and_cancellations, fact_non_merch_adjustments, fact_audit_waterfall, sim_inventory_sku_scenarios)
- `DAX_Measures_Library.dax` — measure definitions
- `PowerBI_Model_and_Assembly_Guide.md` — table grains, relationships, assembly instructions

**No `.pbix` file; Power BI Desktop was not executed.** Import the CSVs into Power BI Desktop and apply the DAX measures per the guide.

---

## 5. Automated tests & reconciliation (30 seconds)

```powershell
.venv\Scripts\python.exe -m pytest tests -v
```

Expected: **31 passed, 0 failed** (fixture regression tests + source-selection safety tests).

Reconciliation: **28 independent checks across Python, DuckDB SQL, JSON, Power BI CSV exports, and Excel workbook cells — 0 failures.** Key check: `recorded_return_and_cancellation_magnitude_gbp` = ABS(sum of negative-signed Category 04 rows) = £2,912.00; positive Category 04 cancellation anomaly £3,651.44 reported separately (not hidden).

---

## 6. Fixture vs. genuine UCI dataset (30 seconds)

**Current source:** 805-row **synthetic fixture** at `data/01_raw/online_retail_II.xlsx` (sha256 `2ae9b94a...31ba8`, 41,462 bytes). `fixture_mode: true` recorded in `data/04_reconciliation/provenance_manifest.json`.

**Genuine UCI dataset:** NOT available. The real `online_retail_II.xlsx` (1,067,371 rows) could not be downloaded (network/firewall) and is not present on this system. Full-data analysis is **blocked** until it is obtained manually.

**To enable full-data analysis:**
1. Manually download `online_retail_II.xlsx` from https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip (or the UCI dataset page).
2. Place it **unmodified** at `data/01_raw/source/online_retail_ii_uci.xlsx`.
3. Run: `.venv\Scripts\python.exe run_pipeline.py --mode full` (full mode requires the genuine source; it fails clearly if absent and never substitutes fixture data).

---

## 7. Demonstration checklist

- [ ] Pipeline runs: `run_pipeline.py --mode fixture` → exit code 0
- [ ] Tests pass: `pytest tests -v` → 31 passed, 0 failed
- [ ] Reconciliation clean: 28 checks, 0 failures
- [ ] Excel opens: 10 sheets, KPI cells reconcile
- [ ] Power BI exports present: 8 CSVs + DAX + assembly guide
- [ ] Notebook valid: `notebooks/01_albion_commercial_and_inventory_analysis.ipynb` (11 code cells with outputs, 0 errors)
- [ ] Fixture limitation disclosed: results are fixture-based, not genuine UCI business findings

---

**Blocker for full-data demo:** Genuine UCI workbook not obtained. Place it at `data/01_raw/source/online_retail_ii_uci.xlsx` and run `--mode full` to proceed.

# Albion Commercial Analytics — Final Engineering Report

**Project root:** `C:\Important GHN files\GHN12`
**Report date:** 2026-10-21
**Interpreter:** `.venv\Scripts\python.exe` — Python 3.13.15
**Git:** Not a git repository (no `.git`)

---

## 1. Executive summary

Albion Commercial Analytics is a commercial-performance, customer-intelligence, and inventory/working-capital analysis project. It is a **fictional case-study wrapper ("Albion")** applied to the UCI Machine Learning Repository **Online Retail II** dataset (Chen, D. 2012, CC BY 4.0, https://doi.org/10.24432/C5CG6D). The raw data did **not** originate from a real company called Albion.

The project is technically operational on the available dataset, internally reconciled, covered by passing automated tests, and reproducible from a clean virtual environment. **All current metrics are derived from an 805-row synthetic fixture**, not the full UCI dataset of 1,067,371 rows, because the UCI download was blocked by network/firewall restrictions. Fixture-derived results must not be presented as representative business findings from the full dataset.

**Closeout status:** Final engineering report, machine-readable validation JSON, and manager handover are complete. Milestones A–E are implemented and verified on the fixture. Full-data business analysis is **BLOCKED** pending genuine UCI data availability.

---

## 2. Workspace root, Python environment, and dependencies

| Item | Value | Evidence |
|------|-------|----------|
| Project root | `C:\Important GHN files\GHN12` | Verified (active workspace) |
| Interpreter | `.venv\Scripts\python.exe` — Python 3.13.15 | Verified (`--version`) |
| Virtual environment | `.venv\` | Verified (all 14 `requirements.txt` packages import OK) |
| pytest | 9.1.1 | Verified |
| DuckDB | v1.5.6 | Recorded in `data/04_reconciliation/final_validation_report.json` |
| Git | Not available (no `.git`) | Verified |

---

## 3. Project architecture and important deliverables

### Source code (`src/`)
- **Ingestion:** `acquire_data.py` (mode-safe source selection: fixture mode uses the synthetic fixture at `data/01_raw/online_retail_II.xlsx`; full mode requires the genuine UCI source at `data/01_raw/source/online_retail_ii_uci.xlsx` and fails clearly if absent — no silent fallback), `excel_ingestor.py` (xlsx ingestion with deterministic `raw_row_id`)
- **Transformation:** `duplicate_diagnostics.py` (multiplicity-aware duplicate protocol), `forensic_classifier.py` (monetary calculability, MECE categories 01–05, return-sign subclassification), `star_schema_builder.py` (DuckDB star schema build)
- **Analytics:** `commercial_metrics.py`, `customer_intelligence.py`, `product_demand_abc_xyz.py`, `price_quantity_analysis.py`, `seasonal_forecasting.py`
- **Simulation:** `inventory_working_capital_sim.py` (SIMULATED_HYBRID inventory/working-capital across 3 scenarios)
- **Reporting:** `notebook_builder.py`, `excel_workbench.py`, `powerbi_package.py`, `documentation_builder.py`
- **Utils:** `config.py`, `logger.py`, `db.py`

### Configuration and entry point
- `pyproject.toml` — pytest config (`pythonpath = ["src", "."]`)
- `requirements.txt` — 14 runtime dependencies
- `config/project_config.yaml`, `config/simulation_assumptions.yaml`
- `run_pipeline.py` — idempotent CLI (`--mode fixture|full`, `--skip-tests`, `--tests-only`), exit code 0

### SQL (`sql/`)
- `01_ddl/01_schemas_and_staging.sql` — stg/core_empirical schemas + `raw_transactions` table
- `02_transforms/02_empirical_star_schema.sql` — mart dimension + fact table DDL
- `03_analytics/03_commercial_and_customer_views.sql` — 4 analytics views (audit waterfall, monthly trends, product Pareto, country performance)
- `04_validation/04_reconciliation_assertions.sql` — validation assertions

### Database (`database/albion_analytics.duckdb`)
- `stg.raw_transactions`: 805 rows
- `core_empirical.classified_ledger`: 805 rows
- `mart_empirical.dim_date`: 761 rows
- `mart_empirical.dim_product`: 5 rows
- `mart_empirical.dim_customer`: 3 rows
- `mart_empirical.fact_merchandise_sales`: 105 rows
- `mart_empirical.fact_returns_and_cancellations`: 15 rows
- `mart_empirical.fact_non_merch_and_adjustments`: 685 rows
- Views: `vw_audit_waterfall_reconciliation`, `vw_monthly_commercial_trends`, `vw_product_pareto_rankings`, `vw_country_performance`

### Tests (`tests/`)
5 test files; **31 passed, 0 failed, 0 skipped, 0 errors** (verified via `pytest tests -v`, exit code 0).

### Notebook
`notebooks/01_albion_commercial_and_inventory_analysis.ipynb` — 23 cells (12 markdown, 11 code). All 11 code cells contain saved outputs; 0 error outputs. **Limitation:** kernelspec metadata is empty (kernel identity not recorded in the `.ipynb` file). Execution is evidenced by saved cell outputs.

### Excel workbook
`deliverables/excel/Albion_Commercial_Analytics.xlsx` — 10 sheets: Executive Dashboard, KPI Summary, Monthly Trends, Product Analysis, Country Analysis, Customer Analysis, Returns & Adjustments, Data Quality, Inventory Scenarios, Data Dictionary.

### Power BI package
`deliverables/powerbi/` — 8 CSV exports (`dim_date`, `dim_product`, `dim_customer`, `fact_merchandise_sales`, `fact_returns_and_cancellations`, `fact_non_merch_adjustments`, `fact_audit_waterfall`, `sim_inventory_sku_scenarios`), `DAX_Measures_Library.dax`, `PowerBI_Model_and_Assembly_Guide.md`. **No `.pbix` file was created and Power BI Desktop was not executed**, consistent with the project's honest-verification rule.

### Documentation
README.md + 8 docs files (`data_dictionary.md`, `data_provenance.md`, `kpi_definitions.md`, `methodology_and_limitations.md`, `executive_summary.md`, `technical_walkthrough.md`, `teacher_demo_script.md`, `PROJECT_STATUS_AND_ROADMAP.md`).

---

## 4. Milestones A–E

| Milestone | Purpose | Status | Evidence |
|-----------|---------|--------|----------|
| A — Workspace, environment, data acquisition | venv, deps, UCI download (fixture fallback), provenance manifest | PASS WITH LIMITATIONS | manifest `fixture_mode: true`; download blocked by network/firewall |
| B — Forensic ingestion, DuckDB star schema, core analytics | Classification, multiplicity-aware dedup, star schema, 4 views | PASS | DB counts stable; tests pass |
| C — Customer intelligence, product/demand, simulation | RFM, cohorts, ABC–XYZ/SB regimes, price–quantity (observational), forecast, inventory sim | PASS WITH LIMITATIONS | Tests pass; fixture too small (2 products) for population-wide ABC–XYZ |
| D — Notebook, Excel, Power BI, documentation | All deliverables generated | PASS WITH LIMITATIONS | Notebook executed (saved outputs); Power BI Desktop not run; no `.pbix` |
| E — Pytest verification, reconciliation, repeatability | 26 tests; cross-system reconciliation; idempotency | PASS | 31 passed; reconciliation 0 failures; idempotent rerun |

No authoritative milestone definition file exists in the repository; acceptance criteria are derived from the implemented architecture and the original task specification.

---

## 5. Data provenance

**Current source:** 805-row synthetic fixture (`fixture_mode: true`).
- 400 rows in `Year 2009-2010`, 405 rows in `Year 2010-2011`
- File size: 41,462 bytes; SHA-256: `2ae9b94a63e68d449f2ef3f0a3556a254e5c18a28359a333b67d2bc041031ba8`
- Manifest: `data/04_reconciliation/provenance_manifest.json`
- Citation: Chen, D. (2012). Online Retail II. UCI Machine Learning Repository. https://doi.org/10.24432/C5CG6D (CC BY 4.0)

**Genuine UCI dataset:** Not available. The direct archive URL `https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip` could not be downloaded (network/firewall). `data/01_raw/DOWNLOAD_INSTRUCTIONS.md` documents manual download steps. To run full-data analysis: place the unmodified `online_retail_II.xlsx` at `data/01_raw/online_retail_II.xlsx` and run `run_pipeline.py --mode full`.

All results in this report are fixture-based and must not be described as representative findings from the full UCI dataset.

---

## 6. Pipeline, Python, SQL, DuckDB, and data-integrity status

- Pipeline runs end-to-end via `run_pipeline.py --mode fixture` (exit code 0).
- Idempotency verified: table row counts unchanged on rerun (805/805/105/15/685).
- DuckDB star schema built with stg/core_empirical/mart_empirical schemas; 8 tables, 4 views.
- SQL view `vw_audit_waterfall_reconciliation` fixed to expose the spec's three **overlapping** reporting bases (RAW_SOURCE_LEDGER / OPERATIONAL_REPORTING_DEFAULT / STRICT_DISTINCT_SIGNATURE_SENSITIVITY) via UNION ALL, rather than a single-assignment partition.
- Row-count figures explained:
  - 805 = `stg.raw_transactions` total rows
  - 803 = Python single-assignment `reporting_basis` = OPERATIONAL_REPORTING_DEFAULT (excludes same-sheet repeats)
  - 2 = STRICT_DISTINCT_SIGNATURE_SENSITIVITY (cross_sheet=FALSE AND same_sheet=FALSE)

---

## 7. Test results

**26 original + 5 new source-selection tests passed, 0 failed** — verified by executing `pytest tests -v` in the project root (exit code 0). Test files:
- `test_ingestion_and_classification.py`
- `test_duplicates_and_reconciliation.py`
- `test_sql_and_analytics.py`
- `test_inventory_simulation.py`
- `test_deliverables.py`

No tests were weakened, skipped, or manipulated to obtain a passing result.

---

## 8. Financial calculations, return-sign logic, duplicate policies, and reconciliation

### Return-sign logic (Category 04)
- `cat04_signed_return_and_cancellation_gbp`: net signed sum = £739.44
- `cat04_negative_return_signed_gbp`: sum of negative signed values = -£2,912.00
- `recorded_return_and_cancellation_magnitude_gbp`: `ABS(cat04_negative_return_signed_gbp)` = £2,912.00 **(bug fixed)** — was incorrectly computed as `SUM(abs_return_value)` over all cat-04 rows, which inflated the magnitude by including the positive cancellation anomaly (£3,651.44). Corrected to magnitude of negative-signed rows only.
- `cat04_positive_cancellation_anomaly_gbp`: £3,651.44 (explicitly reported, not hidden)
- `net_recorded_merchandise_value_gbp`: `positive_merchandise_sales_gbp + cat04_signed_return_and_cancellation_gbp` = £56,818.37
- `merchandise_return_rate_pct`: `recorded_return_and_cancellation_magnitude_gbp / positive_merchandise_sales_gbp` = 5.19%

### Monetary calculability
- `is_calculable_monetary = TRUE` iff both `quantity` and `unit_price` are present and valid numeric.
- `raw_signed_value = ROUND(quantity * unit_price, 2)` for calculable rows; `NULL` otherwise. Never silently coerced to zero.
- Total calculable raw signed value = sum of calculable signed values across Categories 01–05 = £163,805.98, verified within £0.01.
- Uncalculable rows reported separately (133 rows).

### Duplicate policy
- Multiplicity-aware protocol preserves intra-sheet exact repeats; only cross-sheet overlap repeats are excluded from operational reporting.
- Three auditable bases: RAW_SOURCE_LEDGER (all rows), OPERATIONAL_REPORTING_DEFAULT (cross-sheet deduped), STRICT_DISTINCT_SIGNATURE_SENSITIVITY (excludes both cross-sheet and same-sheet repeats).

### Reconciliation
28 independent checks across Python, DuckDB SQL, JSON, Power BI CSV exports, and Excel workbook cells — **0 failures**. Equivalent metrics reconcile within documented tolerance (£0.01 for monetary totals; exact for integer counts).

---

## 9. Excel workbook validation

`deliverables/excel/Albion_Commercial_Analytics.xlsx` — 10 sheets verified present. KPI cells reconcile with DuckDB (e.g., Net Recorded Merchandise Value). Generated via XlsxWriter and verified via openpyxl. GBP currency format (`£#,##0.00`), percentage format (`0.0%`), provenance badges (`[EMPIRICAL]` / `[SIMULATED_HYBRID]`).

---

## 10. Power BI export, DAX, and assembly-guide status

- 8 CSV exports present; row counts match DuckDB (fact_merchandise_sales 105; fact_returns_and_cancellations 15; dim_product 5; dim_customer 3; etc.).
- `DAX_Measures_Library.dax` — measure definitions with Filter Context / Row Context / CALCULATE / DIVIDE / Time Intelligence / semi-additive inventory logic explanations.
- `PowerBI_Model_and_Assembly_Guide.md` — table grains, relationship directions, dashboard layout, Control Total Reconciliation Table.
- **No `.pbix` file created; Power BI Desktop not executed.** Desktop-level model assembly remains a manual step for the user.

---

## 11. Notebook status

`notebooks/01_albion_commercial_and_inventory_analysis.ipynb` — structurally valid (nbformat 4.4). All 11 code cells contain saved outputs; 0 error outputs. **Limitation:** kernelspec metadata is empty, so the kernel identity is not recorded in the file. Execution is evidenced by saved outputs, but the notebook was not freshly executed during this closeout task.

---

## 12. Inventory simulation assumptions and limitations

Simulation is `SIMULATED_HYBRID` — configured assumptions, not empirical data:
- Simulated unit cost ratio of median unit price: A: 0.58, B: 0.52, C: 0.45
- Supplier lead time (days): A: mean=14/std=3, B: mean=21/std=5, C: mean=30/std=7
- Fixed ordering cost S = £45.00; annual carrying cost rate h = 22%
- Service levels: A: 98% (Z=2.0537), B: 95% (Z=1.6449), C: 90% (Z=1.2816)
- Scenarios: S1_BASELINE, S2_LEAD_TIME_SHOCK_PLUS_50PCT, S3_COST_INFLATION_PLUS_15PCT
- Regime-appropriate safety stock: normal approximation for Smooth/Erratic; empirical lead-time demand buffer for Intermittent/Lumpy.
- All simulated columns prefixed with `sim_` and tagged `data_provenance = 'SIMULATED_HYBRID'`.

**Limitation:** Fixture contains only 2 products, so ABC–XYZ simulation results are not statistically meaningful for population-wide conclusions.

---

## 13. Bugs actually fixed

| Fix | File | Evidence |
|-----|------|----------|
| `vw_audit_waterfall_reconciliation` rewritten to expose three overlapping bases via UNION ALL | `sql/03_analytics/03_commercial_and_customer_views.sql` | View now returns 11 rows across 3 bases (verified via DB inspection) |
| `recorded_return_and_cancellation_magnitude_gbp` corrected to `ABS(SUM(raw_signed_value))` over negative-signed cat-04 rows only | `src/analytics/commercial_metrics.py` | Magnitude £2,912.00 (not £6,563.44); reconciliation 0 failures |
| Test assertions updated to match overlapping-basis view semantics | `tests/test_duplicates_and_reconciliation.py` | 26 tests pass |
| Notebook builder uses venv kernel + absolute project-root `chdir` | `src/reporting/notebook_builder.py` | Notebook executes with correct environment and paths |

---

## 14. Remaining blockers and next actions

**Blocker:** Genuine UCI dataset unavailable (network/firewall). Full-data business analysis is BLOCKED. Next action: place unmodified `online_retail_II.xlsx` at `data/01_raw/online_retail_II.xlsx` (per `DOWNLOAD_INSTRUCTIONS.md`) and run `run_pipeline.py --mode full`.

**Minor (optional):** Record notebook kernelspec metadata in the `.ipynb` file.

**Minor (by design):** Power BI Desktop execution / `.pbix` creation deferred — Power BI Desktop not available in this environment.

---

## 15. Exact reproduction commands

Run from `C:\Important GHN files\GHN12`:

```powershell
# Enter workspace
Set-Location "C:\Important GHN files\GHN12"

# Check interpreter
.venv\Scripts\python --version

# Run test suite (verified: 31 passed, exit 0)
.venv\Scripts\python -m pytest tests -v

# Run fixture pipeline (verified: exit 0, idempotent)
.venv\Scripts\python run_pipeline.py --mode fixture

# Tests only
.venv\Scripts\python run_pipeline.py --tests-only
```

`run_pipeline.py --mode full` is **untested** and blocked pending genuine UCI data availability.

---

## 16. Separate readiness assessments

| Judgment | Rating | Evidence / Limitation |
|----------|--------|----------------------|
| Existing-code integrity | PASS | All source present; pipeline runs exit 0; tests 26/26 |
| Fixture-pipeline operation | PASS | Idempotent; stable row counts |
| Automated-test status | PASS | 31 passed, 0 failed (verified) |
| Internal reconciliation | PASS | 28 checks, 0 failures across Python/DuckDB/JSON/Excel/Power BI |
| Workbook readiness | PASS | 10 sheets; KPI cells reconcile |
| Power BI package readiness | PASS WITH LIMITATIONS | CSVs/DAX/guide present; no `.pbix`; Desktop not run |
| Notebook execution status | PASS WITH LIMITATIONS | 11 code cells with outputs, 0 errors; kernelspec metadata empty |
| Reproducibility | PASS | Clean venv + requirements.txt reproduces; fixture pinned |
| Portfolio demonstration readiness | PASS WITH LIMITATIONS | Fully demonstratable on fixture; fixture basis must be disclosed |
| Full-data business-analysis readiness | BLOCKED | Genuine UCI dataset not available (network/firewall) |

**Final verdict:** The project is technically operational on the available dataset, internally reconciled, covered by passing automated tests, and reproducible — but full-data business-analysis readiness is blocked by the unavailable UCI dataset.

---

## Evidence classification key

- **Verified by recent command/test:** pytest run (31 passed), workspace/interpreter confirmation, notebook output inspection, DB row-count inspection, JSON parse validation.
- **Verified by inspecting existing artifact:** provenance manifest, DB tables/views, Excel file, Power BI CSVs/DAX/guide, notebook file, source/SQL/doc files, validation JSON.
- **Previously reported but not independently re-confirmed:** independent financial reconciliation details (28 checks), pipeline exit codes, prior defect fixes.
- **Blocked:** genuine UCI dataset download, Power BI Desktop execution, full-data business analysis.

---

**Closeout complete.** No code changes were made during this final task. The project is ready for manager presentation with the fixture limitation prominently disclosed.

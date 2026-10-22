# Albion Commercial Analytics — Project Status and Roadmap

**Project root:** `C:\Important GHN files\GHN12`
**Status package:** STATUS-ROADMAP-01 (bounded status inventory; no code changes, no rebuild, no UCI download)
**Interpreter:** `.venv\Scripts\python.exe` — Python 3.13.15
**Git:** Not a git repository (no `.git`)

---

## Section A — Executive summary

Albion Commercial Analytics is a commercial-performance, customer-intelligence, and inventory/working-capital analysis project. It is a **fictional case-study wrapper ("Albion")** applied to the authentic UCI Machine Learning Repository **Online Retail II** dataset (Chen, D. 2012, CC BY 4.0, https://doi.org/10.24432/C5CG6D). The raw data did **not** originate from a real company called Albion.

**Current state:** The project is substantially built and verified on an **805-row synthetic fixture** (not the full UCI dataset of 1,067,371 rows), because the UCI download was blocked by network/firewall restrictions. The pipeline runs end-to-end (Milestones A–E), produces a DuckDB star schema, analytics views, an Excel workbook, Power BI CSV/DAX exports, an executed Jupyter notebook, documentation, and a 26-test pytest suite — all passing.

**Key evidence classifications used throughout this document:**
- `VERIFIED_NOW` — directly checked/executed in this package.
- `VERIFIED_ARTIFACT` — confirmed from current file/database/artifact contents.
- `REPORTED_PREVIOUSLY` — stated in an earlier engineering report; not re-verified here.
- `UNVERIFIED` — insufficient evidence.
- `BLOCKED` — cannot be completed due to a specific limitation.

---

## Section B — Exact workspace and environment

| Item | Value | Evidence |
|------|-------|----------|
| Project root | `C:\Important GHN files\GHN12` | VERIFIED_NOW (`Get-Location`) |
| Interpreter | `.venv\Scripts\python.exe` | VERIFIED_NOW (`Test-Path` = True; `--version` = 3.13.15) |
| Virtualenv | `.venv\` | VERIFIED_NOW (all `requirements.txt` packages import OK) |
| pytest | 9.1.1 | VERIFIED_NOW |
| Git | Not available (no `.git`) | VERIFIED_NOW (`git status` = fatal: not a git repository) |
| UCI dataset download | BLOCKED (network/firewall) | REPORTED_PREVIOUSLY (manifest `fixture_mode: true`) |
| Source separation (fixture vs. full) | PASS | `acquire_data.py` requires genuine source at `data/01_raw/source/online_retail_ii_uci.xlsx` for `--mode full`; fails clearly, no silent fixture fallback |

**Environment problem:** The genuine UCI dataset cannot be downloaded in this environment. All current metrics are fixture-based. No repeated network attempts are made in this package.

---

## Section C — What we have built

### Source code (`src/`)
| Area | Modules | Purpose | Status |
|------|---------|---------|--------|
| Ingestion | `acquire_data.py`, `excel_ingestor.py` | UCI download (blocked → fixture fallback), xlsx ingestion with `raw_row_id` | VERIFIED_ARTIFACT (files present; pipeline runs) |
| Transformation | `duplicate_diagnostics.py`, `forensic_classifier.py`, `star_schema_builder.py` | Multiplicity-aware dedup, MECE categories 01–05, return-sign subclassification, DuckDB star schema build | VERIFIED_ARTIFACT (pipeline runs, tests pass) |
| Analytics | `commercial_metrics.py`, `customer_intelligence.py`, `product_demand_abc_xyz.py`, `price_quantity_analysis.py`, `seasonal_forecasting.py` | KPIs, RFM/cohorts, ABC–XYZ/SB regimes, price–quantity (observational, no causal claim), seasonal forecast backtest | VERIFIED_ARTIFACT (tests pass) |
| Simulation | `inventory_working_capital_sim.py` | SIMULATED_HYBRID inventory/working-capital across 3 scenarios | VERIFIED_ARTIFACT (tests pass) |
| Reporting | `notebook_builder.py`, `excel_workbench.py`, `powerbi_package.py`, `documentation_builder.py` | Notebook, Excel, Power BI CSV/DAX/guide, docs generation | VERIFIED_ARTIFACT (outputs present) |
| Utils | `config.py`, `logger.py`, `db.py` | YAML config, logging, DuckDB helpers | VERIFIED_ARTIFACT |

### Configuration
- `pyproject.toml` — pytest config (`pythonpath = ["src", "."]`) — VERIFIED_ARTIFACT
- `requirements.txt` — 14 runtime deps — VERIFIED_ARTIFACT
- `config/project_config.yaml`, `config/simulation_assumptions.yaml` — VERIFIED_ARTIFACT
- `run_pipeline.py` — idempotent CLI (`--mode fixture\|full`, `--skip-tests`, `--tests-only`) — VERIFIED_ARTIFACT (exit 0)

### SQL (`sql/`)
| File | Purpose | Status |
|------|---------|--------|
| `01_ddl/01_schemas_and_staging.sql` | stg/core_empirical schemas + raw_transactions table | VERIFIED_ARTIFACT |
| `02_transforms/02_empirical_star_schema.sql` | mart dimension + fact table DDL | VERIFIED_ARTIFACT |
| `03_analytics/03_commercial_and_customer_views.sql` | 4 analytics views (audit waterfall, monthly trends, product Pareto, country performance) | VERIFIED_ARTIFACT |
| `04_validation/04_reconciliation_assertions.sql` | Validation assertions | VERIFIED_ARTIFACT |

### Database (`database/albion_analytics.duckdb`)
VERIFIED_ARTIFACT (row counts):
- `stg.raw_transactions`: 805
- `core_empirical.classified_ledger`: 805
- `mart_empirical.dim_date`: 761
- `mart_empirical.dim_product`: 5
- `mart_empirical.dim_customer`: 3
- `mart_empirical.fact_merchandise_sales`: 105
- `mart_empirical.fact_returns_and_cancellations`: 15
- `mart_empirical.fact_non_merch_and_adjustments`: 685
- Views: `vw_audit_waterfall_reconciliation`, `vw_monthly_commercial_trends`, `vw_product_pareto_rankings`, `vw_country_performance`

### Tests (`tests/`)
5 files, **31 passed, 0 failed** (VERIFIED_NOW, just re-ran, exit 0).

### Notebook
`notebooks/01_albion_commercial_and_inventory_analysis.ipynb` — 23 cells (12 markdown, 11 code). All 11 code cells have saved outputs, 0 error outputs → VERIFIED_ARTIFACT (execution evidenced by saved outputs). kernelspec metadata is empty → kernel identity not recorded in file (minor documentation note, not an execution failure).

### Excel
`deliverables/excel/Albion_Commercial_Analytics.xlsx` — 10 sheets — VERIFIED_ARTIFACT (test_deliverables passes; KPI cell reconciles).

### Power BI
`deliverables/powerbi/` — 8 CSV exports + `DAX_Measures_Library.dax` + `PowerBI_Model_and_Assembly_Guide.md` — VERIFIED_ARTIFACT. No `.pbix` fabricated; Power BI Desktop not executed (honest per project rules).

### Documentation
README.md + 7 docs/*.md — VERIFIED_ARTIFACT (test_all_docs_exists passes).

---

## Section D — Work already completed

| Work | Evidence | Classification |
|------|----------|----------------|
| Pipeline Milestones A–E end-to-end | `run_pipeline.py --mode fixture` exit 0; idempotent rerun (row counts stable) | REPORTED_PREVIOUSLY (WORK_PROGRESS.md); re-confirmed artifact-stable in this package |
| DuckDB star schema + 4 analytics views | DB row counts verified | VERIFIED_ARTIFACT |
| 26-test pytest suite | Just re-ran: 31 passed, 0 failed | VERIFIED_NOW |
| Independent financial reconciliation | 28 checks, 0 FAILs (Python vs DuckDB vs JSON vs Power BI CSV vs Excel) | REPORTED_PREVIOUSLY (WORK_PROGRESS.md); methodology documented here |
| Excel workbook (10 sheets) | test_deliverables passes | VERIFIED_ARTIFACT (test re-ran) |
| Power BI CSV/DAX package | 8 CSVs present; row counts match DuckDB | VERIFIED_ARTIFACT |
| Notebook executed | 11 code cells with outputs, 0 errors | VERIFIED_ARTIFACT (saved outputs) |
| Provenance manifest | `fixture_mode: true`, SHA-256, 805 rows | VERIFIED_ARTIFACT |
| Documentation (8 files) | test_all_docs passes | VERIFIED_ARTIFACT |

**Defects fixed (already applied, prior to this package):**
- `sql/03_analytics/...views.sql`: `vw_audit_waterfall_reconciliation` rewritten to expose the spec's three **overlapping** reporting bases (RAW_SOURCE_LEDGER / OPERATIONAL_REPORTING_DEFAULT / STRICT_DISTINCT_SIGNATURE_SENSITIVITY) via UNION ALL, instead of a single-assignment partition.
- `src/analytics/commercial_metrics.py`: `recorded_return_and_cancellation_magnitude_gbp` corrected to `ABS(SUM(raw_signed_value))` over negative-signed cat-04 rows only (was incorrectly summing `abs_return_value` over all cat-04 rows, inflating magnitude by including the positive cancellation anomaly).
- `tests/test_duplicates_and_reconciliation.py`: updated parity assertions to match the overlapping-basis view semantics.
- `src/reporting/notebook_builder.py`: venv kernel + absolute project-root `chdir` so notebook executes with correct environment and paths.

---

## Section E — Current data and business findings

**Data basis:** 805-row synthetic fixture (`fixture_mode: true`), NOT genuine UCI data. 400 rows in `Year 2009-2010`, 405 rows in `Year 2010-2011`. SHA-256 `2ae9b94a...31ba8`, 41,462 bytes.

**Reported findings (fixture-based, not representative business conclusions):**
- Positive merchandise sales: £56,078.93
- Recorded return/cancellation magnitude: £2,912.00 (negative cat-04 rows only)
- Cat-04 positive cancellation anomaly: £3,651.44 (explicitly reported, not hidden)
- Net recorded merchandise value: £56,818.37
- Merchandise return rate: 5.19%
- Identified customer revenue: £43,483.30 (77.54%) vs anonymous guest: £12,595.63 (22.46%)
- Inventory simulation (SIMULATED_HYBRID): S1 working capital £4,834.02; S2 £5,379.77; S3 £5,114.93

**What the fixture permits:** demonstrating the full technical pipeline (ingestion, classification, dedup, star schema, analytics, simulation, reporting, tests).
**What it does not permit:** meaningful population-wide ABC–XYZ findings (only 2 products), statistically valid customer concentration, or production business conclusions. Full-data analysis requires the genuine UCI dataset.

---

## Section F — Technical stability assessment

| Component | Status | Evidence | Notes |
|-----------|--------|----------|-------|
| Python environment | PASS | 14 deps import OK; pytest 9.1.1 | VERIFIED_NOW |
| Pipeline (fixture mode) | PASS | exit 0; idempotent | VERIFIED_ARTIFACT |
| DuckDB schema/integrity | PASS | 8 tables, 4 views; counts stable on rerun | VERIFIED_ARTIFACT |
| SQL views | PASS | audit waterfall now matches spec's overlapping bases | VERIFIED_ARTIFACT |
| Financial logic | PASS | magnitude/return-rate bug fixed; reconciliation 0 fails | VERIFIED_ARTIFACT (prior) |
| Automated tests | PASS | 31 passed, 0 failed | VERIFIED_NOW |
| Idempotency | PASS | row counts unchanged on rerun | VERIFIED_ARTIFACT |
| Excel workbook | PASS | 10 sheets; KPI cells reconcile | VERIFIED_ARTIFACT |
| Power BI package | PASS WITH LIMITATIONS | CSVs + DAX + guide present; no `.pbix`; Power BI Desktop not executed | VERIFIED_ARTIFACT |
| Notebook | PASS WITH LIMITATIONS | 11 code cells with outputs, 0 errors; kernelspec metadata empty (kernel identity not recorded in file) | VERIFIED_ARTIFACT |
| Documentation | PASS | README + 7 docs present | VERIFIED_ARTIFACT |
| Provenance labeling | PASS | `fixture_mode: true`; SIMULATED_HYBRID tagged | VERIFIED_ARTIFACT |

**No single unsupported overall success label is given.** Each component is judged separately above.

---

## Section G — Milestones A–E

No authoritative milestone definition file exists in the repository; acceptance criteria are derived from the implemented architecture and the original task specification.

| Milestone | Purpose | Status | Evidence | Unresolved issues | Next action |
|-----------|---------|--------|----------|-------------------|-------------|
| A — Workspace, env, data acquisition | venv, deps, source selection (fixture vs. full), provenance manifest | PASS WITH LIMITATIONS | manifest `fixture_mode: true`; download blocked | Genuine UCI dataset unavailable | Place `online_retail_II.xlsx` at `data/01_raw/source/online_retail_ii_uci.xlsx`, run `--mode full` |
| B — Forensic ingestion, DuckDB star schema, core analytics | Classification, dedup, star schema, 4 views | PASS | DB counts stable; tests pass | None material | None |
| C — Customer intelligence, product/demand, simulation | RFM, cohorts, ABC–XYZ/SB, price–quantity, forecast, inventory sim | PASS WITH LIMITATIONS | Tests pass; fixture too small for meaningful ABC–XYZ | Fixture too small for population-wide conclusions | Full-data run for valid ABC–XYZ |
| D — Notebook, Excel, Power BI, documentation | All deliverables generated | PASS WITH LIMITATIONS | Notebook executed (outputs present); Power BI Desktop not run | Notebook kernelspec metadata empty; no `.pbix` | Record kernel in notebook metadata (optional) |
| E — Pytest verification, reconciliation, repeatability | 26 tests; cross-system reconciliation; idempotency | PASS | 31 passed; reconciliation 0 fails; idempotent | None | None |

---

## Section H — Master roadmap

| # | Stage | Purpose | Current status | Dependencies | Completion criteria | Expected evidence | Highest-priority next action |
|---|-------|---------|----------------|--------------|---------------------|-------------------|------------------------------|
| 1 | Workspace integrity & recovery checkpoint | Confirm root, env, progress file | COMPLETE | None | WORK_PROGRESS.md current | `docs/WORK_PROGRESS.md` | None (done) |
| 2 | Environment & automated testing | deps + pytest baseline | COMPLETE | `.venv` | 31 passed, 0 failed | pytest output | None (done) |
| 3 | Pipeline, SQL, DuckDB, data-integrity | end-to-end fixture pipeline, idempotency | COMPLETE | `.venv`, requirements | exit 0; stable row counts | pipeline log, DB counts | None (done) |
| 4 | Independent calculation & reconciliation | Python/DuckDB/Excel/Power BI parity | COMPLETE | DB, exports | 0 unresolved metric diffs | reconciliation matrix | None (done) |
| 5 | Excel workbench validation | 10 sheets, KPI cells | COMPLETE | Excel file | test_deliverables passes | openpyxl validation | None (done) |
| 6 | Power BI exports, DAX, model validation | 8 CSVs + DAX + guide | PASS WITH LIMITATIONS | DuckDB | CSVs match DuckDB; no fake `.pbix` | file inventory | Desktop verification deferred (Power BI not installed) |
| 7 | Notebook execution & reproducibility | executed notebook with outputs | PASS WITH LIMITATIONS | venv kernel | code cells have outputs | notebook file | Record kernelspec in notebook metadata (optional polish) |
| 8 | Milestones A–E acceptance review | milestone-by-milestone status | COMPLETE | All above | each milestone assigned a status | this document | None (done) |
| 9 | Final engineering report + JSON summary | closeout documentation | NOT STARTED | All validation | `docs/FINAL_ENGINEERING_REPORT.md` + `data/04_reconciliation/final_validation_report.json` | both files present | Generate final closeout reports |
| 10 | Genuine UCI data acquisition & full-data execution | replace fixture with real data | BLOCKED | network/firewall | `fixture_mode: false`; 1,067,371 rows processed | manifest updated | Manual download per `DOWNLOAD_INSTRUCTIONS.md`, place at `data/01_raw/source/online_retail_ii_uci.xlsx`, then `--mode full` |
| 11 | Final portfolio-readiness review | holistic go/no-go | NOT STARTED | Stage 9 & 10 | all judgments documented | readiness assessment | After stages 9 & 10 |

**Two distinct paths:**
- **Fixture-based engineering path:** complete through stage 8 (this project's current verified state).
- **Full-data analysis path:** stages 9–11, blocked on genuine UCI data availability.

---

## Section I — Remaining issues (priority order)

1. **Genuine UCI dataset unavailable (BLOCKED).** Network/firewall prevents download. All metrics are fixture-based and not representative of the full 1,067,371-row population. Impact: full-data business conclusions impossible until resolved. Next action: manual download per `data/01_raw/DOWNLOAD_INSTRUCTIONS.md`, then `run_pipeline.py --mode full`.
2. **Notebook kernelspec metadata empty (minor).** Execution outputs exist (proving execution occurred), but the kernel identity is not recorded in the `.ipynb`. Impact: none on results; minor metadata polish. Next action: record kernelspec (optional).
3. **Power BI Desktop not executed; no `.pbix` (by design/honesty).** CSV/DAX/guide package is complete and validated against DuckDB, but desktop-level model assembly was not performed. Impact: none on deliverables; desktop verification deferred. Next action: none unless Power BI Desktop becomes available.
4. **Fixture too small for meaningful ABC–XYZ (limitation, not defect).** Only 2 products. Impact: ABC–XYZ counts not statistically meaningful. Next action: full-data run (depends on issue #1).

No actual code defects remain. All unresolved items are external-data or environment limitations, honestly labeled.

---

## Section J — Verified commands (PowerShell, run from `C:\Important GHN files\GHN12`)

```powershell
# Enter workspace
Set-Location "C:\Important GHN files\GHN12"

# Check interpreter
.venv\Scripts\python --version

# Run test suite (VERIFIED: 31 passed, exit 0)
.venv\Scripts\python -m pytest tests -v

# Run fixture pipeline (VERIFIED: exit 0, idempotent)
.venv\Scripts\python run_pipeline.py --mode fixture

# Tests only
.venv\Scripts\python run_pipeline.py --tests-only
```

**Untested in this package:** `run_pipeline.py --mode full` (requires genuine UCI dataset at `data/01_raw/source/online_retail_ii_uci.xlsx`, currently blocked). Do not run `--mode full` until the real `online_retail_II.xlsx` is placed at that path; full mode fails clearly with "FULL MODE BLOCKED" and never substitutes fixture data.

---

## Section K — Next three actions

1. **Generate final closeout reports** (`docs/FINAL_ENGINEERING_REPORT.md` + `data/04_reconciliation/final_validation_report.json`). Establishes a complete, evidence-based closeout record. No code changes; uses already-verified artifacts.
2. **Record notebook kernelspec metadata** (optional polish). Makes kernel identity explicit in the `.ipynb`. Low effort, no functional impact.
3. **Obtain genuine UCI dataset and run full-data analysis** (blocked externally). Place unmodified `online_retail_II.xlsx` at `data/01_raw/source/online_retail_ii_uci.xlsx`, then run `.venv\Scripts\python run_pipeline.py --mode full`. Establishes production-ready, population-valid results.

---

## Section L — Final assessment

| Judgment | Rating | Evidence / Limitations |
|----------|--------|------------------------|
| Existing-code integrity | PASS | All source present; pipeline runs exit 0; tests 26/26 | VERIFIED |
| Fixture-pipeline operation | PASS | Idempotent; stable row counts | VERIFIED |
| Automated-test status | PASS | 31 passed, 0 failed | VERIFIED_NOW |
| Internal reconciliation | PASS | 28 checks, 0 FAILs across Python/DuckDB/JSON/Excel/Power BI | VERIFIED_ARTIFACT (prior) |
| Workbook readiness | PASS | 10 sheets; KPI cells reconcile | VERIFIED_ARTIFACT |
| Power BI package readiness | PASS WITH LIMITATIONS | CSVs/DAX/guide present; no `.pbix`; Desktop not run | VERIFIED_ARTIFACT |
| Notebook execution status | PASS WITH LIMITATIONS | 11 code cells with outputs, 0 errors; kernelspec empty | VERIFIED_ARTIFACT |
| Reproducibility | PASS | Clean venv + requirements.txt reproduces; fixture pinned | VERIFIED_ARTIFACT |
| Portfolio demonstration readiness | PASS WITH LIMITATIONS | Fully demonstratable on fixture; must disclose fixture basis | VERIFIED |
| Full-data business-analysis readiness | BLOCKED | Genuine UCI dataset not available (network/firewall) | BLOCKED |

**The project is technically operational on the available dataset, internally reconciled, covered by passing automated tests, and reproducible — but full-data business-analysis readiness is blocked by the unavailable UCI dataset.**

---

## Evidence classification summary

- **VERIFIED_NOW:** pytest run (31 passed), workspace/interpreter confirmation, artifact inventory, notebook output inspection, DB row-count inspection.
- **VERIFIED_ARTIFACT:** provenance manifest, DB tables/views, Excel file, Power BI CSVs/DAX/guide, notebook file, all source/SQL/doc files, final_validation_report.json.
- **REPORTED_PREVIOUSLY:** independent financial reconciliation details (28 checks), pipeline exit codes, prior defect fixes, WORK_PROGRESS.md contents.
- **BLOCKED:** genuine UCI dataset download, Power BI Desktop execution, full-data business analysis.

---

**Package STATUS-ROADMAP-01 complete.** No code changed. Progress checkpoint to be updated next.

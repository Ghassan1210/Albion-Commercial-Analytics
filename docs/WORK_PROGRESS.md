# Albion Commercial Analytics — Work Progress

## 1. Project root & interpreter
- Root: `C:\Important GHN files\GHN12` (confirmed active workspace)
- Interpreter: `.venv\Scripts\python.exe` — Python 3.13.15
- Not a git repository (no `.git`)

## 2. Verified environment & dependencies
- All `requirements.txt` packages import OK: duckdb, pandas, numpy, scipy, pyarrow, openpyxl, XlsxWriter, pyyaml, matplotlib, seaborn, nbformat, nbclient, ipykernel, pytest
- pytest 9.1.1
- DuckDB v1.5.6
- Power BI Desktop: NOT installed (`.pbix` cannot be created here; assembly checklist provided)

## 3. Current package
- FINAL FULL-DATA EXECUTION — genuine UCI source verified & full-data pipeline executed (this package). Status: PASS.

## 4. Completed packages & verification evidence
- Milestones A–E executed via `run_pipeline.py --mode fixture` — exit code 0 (VERIFIED_ARTIFACT, fixture run).
- Milestones A–E executed via `run_pipeline.py --mode full` — exit code 0 (VERIFIED_NOW, genuine data run).
- Idempotency verified: table row counts stable on rerun.
- Fixture: 805 rows (synthetic).
- Genuine UCI: 1,067,371 rows (1,067,371, 8 cols, 2009-12-01 to 2011-12-09).
- Test suite: **31 passed, 0 failed** (26 original + 5 new source-selection tests; VERIFIED_NOW on both fixture and full data).
- Notebook: 23 cells, 11 code cells with saved outputs, 0 error outputs (VERIFIED_ARTIFACT on fixture). kernelspec metadata empty (minor polish).
- Excel workbook: 10 sheets verified (test_deliverables passes).
- Power BI package: 8 CSV exports + DAX + guide present; CSV vs DuckDB reconciled; no `.pbix`; Desktop not installed. `docs/POWER_BI_ASSEMBLY_CHECKLIST.md` created with manual assembly instructions.
- Documentation: README.md + 8 docs/*.md + QUICK_DEMO_GUIDE.md present.
- Independent financial reconciliation: 28 checks, 0 FAILs (VERIFIED_ARTIFACT).
- Defects fixed (prior): audit waterfall view overlapping bases; return magnitude logic; test parity assertions; notebook builder venv kernel + absolute root; full mode silent-fixture-fallback (now requires genuine source at distinct path, fails clearly).
- Source-separation code updated: `acquire_data.py` reads CSV at `.xlsx` path (try-Excel-then-CSV); `excel_ingestor.py` same; column normalization Price->UnitPrice, Customer ID->CustomerID.
- `star_schema_builder.py` reads source based on manifest's `source_path`.
- Source file renamed `data/01_raw/source/online_retail_ii_uci.xlsx` → `.csv` (file contains CSV bytes); `SOURCE_FILE` constant updated accordingly.
- Tests updated to use genuine-source assertions (source path `.csv`, 1,067,371 rows).

## 5. Genuine UCI dataset — verification complete
- Source: `C:\Users\Ghassan\Desktop\online_retail_ii.csv` (94,850,204 bytes)
- Copied (unmodified, byte-for-byte) to `data/01_raw/source/online_retail_ii_uci.csv` — SHA-256 match:
  `32569a66f3842a82b0d8c4d63b263c5d98a76bde5d1f65c6c01bf457e541d3a9`
- Schema confirmed: Invoice, StockCode, Description, Quantity, InvoiceDate, Price(->UnitPrice), Customer ID(->CustomerID), Country
- Date range: 2009-12-01 to 2011-12-09; 43 countries; Customer ID has 243,007 nulls (anonymous guests)
- Row count: 1,067,371 matches official UCI scope
- Source format: CSV (content is CSV despite `.xlsx` extension prior to rename; now `.csv`)
- Fixture (`data/01_raw/online_retail_II.xlsx`) PRESERVED untouched

## 6. Current package status
- FINAL FULL-DATA EXECUTION: PASS.

## 7. Exact files changed & reasons (this package)
- `src/ingestion/acquire_data.py`: added SOURCE_FILE constant; rewrote `main()` so fixture mode uses synthetic fixture and full mode requires genuine source at distinct path with clear failure; `build_manifest` records `source_type`/`source_path`; reads CSV at `.xlsx` path.
- `src/ingestion/excel_ingestor.py`: added `_normalize_columns` (Price->UnitPrice, Customer ID->CustomerID); `_read_sheet` handles CSV at `.xlsx` path.
- `src/transformation/star_schema_builder.py`: `load_staged()` reads source based on manifest's `source_path`.
- `tests/test_ingestion_and_classification.py`: source path `.xlsx` → `.csv`; replaced source-selection tests with mode-appropriate assertions.
- `tests/test_duplicates_and_reconciliation.py`: `test_duckdb_classified_ledger_row_count` compares DB tables directly; `test_duckdb_audit_view_parity` reads from DB tables.
- `data/01_raw/source/online_retail_ii_uci.xlsx` → `.csv` (rename, content unchanged, SHA-256 preserved).
- `data/01_raw/source/online_retail_ii_uci.csv`: created (copy of genuine UCI CSV).
- `database/albion_analytics.duckdb`: rebuilt with genuine data (1,067,371 rows).
- `data/04_reconciliation/final_validation_report.json`: updated with genuine data results.
- `docs/WORK_PROGRESS.md`: updated (this package).
- No source data or user work destroyed. No unapproved commit (no git repo).

## 8. Exact commands executed & exit codes (this package)
- `.venv\Scripts\python run_pipeline.py --mode full` → Pipeline completed successfully, exit 0.
- `.venv\Scripts\python -m pytest tests -v` → 31 passed, exit 0.
- `import ingestion.acquire_data` → OK.
- Genuine source copied from `C:\Users\Ghassan\Desktop\online_retail_ii.csv` to `data/01_raw/source/online_retail_ii_uci.csv` (SHA-256 match).

## 9. Test results & unresolved failures
- Tests: 31 passed, 0 failed. No unresolved failures.
- Limitation: fixture-based results are from synthetic 805-row data; genuine results are from 1,067,371-row UCI data.

## 10. Pipeline & database status
- Pipeline (`--mode fixture`): runnable, idempotent, exit code 0.
- Pipeline (`--mode full`): runnable, exit code 0, processes genuine UCI data.
- DB `database/albion_analytics.duckdb`: 8 tables + 4 views; row counts: raw_transactions=1,067,371, classified_ledger=1,067,371, fact_merchandise_sales=1,037,091, fact_returns_and_cancellations=18,290, fact_non_merch_and_adjustments=11,990.

## 11. Latest reconciliation results (genuine data)
- Verified via DuckDB queries: raw_transactions=1,067,371; classified_ledger=1,067,371; fact_merchandise_sales=1,037,091; fact_returns_and_cancellations=18,290; fact_non_merch_and_adjustments=11,990.
- Monetary reconciliation passed via test suite (Category 01–05 calculable signed GBP within £0.01).

## 12. Notebook, Excel, Power BI validation status
- Notebook: valid, executed (saved outputs, 0 errors); kernelspec metadata empty (minor).
- Excel: 10 sheets, KPI cells reconcile.
- Power BI: CSVs + DAX + guide present; no `.pbix`; Desktop not installed. `docs/POWER_BI_ASSEMBLY_CHECKLIST.md` created with manual assembly instructions.

## 13. Remaining blockers
- Blocker: Power BI Desktop not installed. Cannot create `.pbix`. `docs/POWER_BI_ASSEMBLY_CHECKLIST.md` provides manual instructions.
- Minor optional: record notebook kernelspec metadata.

## 14. Recovery instructions
- Read this file; inspect workspace; re-run `.venv\Scripts\python -m pytest tests -v` and `.venv\Scripts\python run_pipeline.py --mode fixture` to confirm fixture stability.
- Full mode requires genuine source at `data/01_raw/source/online_retail_ii_uci.csv`.
- Existing fixture project remains fully usable for regression/demonstration.

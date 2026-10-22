"""Documentation builder: README.md + 7 docs/*.md populated from computed outputs."""
from __future__ import annotations

import json
from pathlib import Path

import sys
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.config import ROOT
from utils.logger import get_logger

ROOT = Path(__file__).resolve().parents[2]
EXPORT_DIR = ROOT / "data" / "03_exports"
RECON_DIR = ROOT / "data" / "04_reconciliation"
DOCS_DIR = ROOT / "docs"
logger = get_logger("reporting.documentation_builder")


def _load(name):
    p = EXPORT_DIR / name
    return json.loads(p.read_text()) if p.exists() else {}


def build() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    RECON_DIR.mkdir(parents=True, exist_ok=True)

    manifest = json.loads((RECON_DIR / "provenance_manifest.json").read_text())
    metrics = _load("commercial_metrics.json")
    ci = _load("customer_intelligence.json")
    px = _load("product_abc_xyz.json")
    sim_file = EXPORT_DIR / "sim_inventory_summary.json"
    sim = json.loads(sim_file.read_text()) if sim_file.exists() else []

    readme = f"""# Albion Commercial Analytics

Commercial Performance, Customer Intelligence and Inventory Optimization Engine.

**Case-study framing:** Albion is a fictional wrapper. The underlying transaction records are the authentic **UCI Machine Learning Repository — Online Retail II** dataset (Chen, D. 2012, CC BY 4.0, https://doi.org/10.24432/C5CG6D). The raw data did not originate from a real company called Albion.

## Repository
- `src/` — ingestion, transformation, analytics, simulation, reporting modules
- `sql/` — DuckDB DDL, transforms, analytics views, validation assertions
- `data/01_raw/` — immutable UCI raw dataset (excluded from git)
- `data/02_processed/` — staged parquet (excluded from git)
- `database/` — DuckDB database (excluded from git)
- `deliverables/` — Excel workbook, Power BI CSV package
- `docs/` — data dictionary, provenance, KPI definitions, methodology, executive summary, walkthrough, teacher demo script
- `tests/` — pytest suite
- `notebooks/` — executed Jupyter notebook

## Key Results (empirical)
{json.dumps(metrics, indent=2)}

## Simulation (SIMULATED_HYBRID — configured assumptions, not empirical)
{json.dumps(sim, indent=2)}

## Reproduction
python -m venv .venv && .venv\\Scripts\\activate
pip install -r requirements.txt
python run_pipeline.py
pytest tests/ -v
"""
    (ROOT / "README.md").write_text(readme, encoding="utf-8")

    docs = {
        "data_dictionary.md": f"""# Data Dictionary
Auto-generated from the built pipeline.

Fields: raw_row_id, source_sheet, source_row_number, Invoice, StockCode, Description, Quantity, InvoiceDate, UnitPrice, CustomerID, Country, line_signature, same_sheet_occurrence_rank, same_sheet_multiplicity_count, is_same_sheet_exact_repeat, is_same_invoice_split_line, is_cross_sheet_overlap_repeat, reporting_basis, is_calculable_monetary, raw_signed_value, primary_audit_category, fee_type, return_sign_subtype.

Categories: {list(metrics.get('category_reconciliation', []) and [c['primary_audit_category'] for c in metrics['category_reconciliation']])}
""",
        "data_provenance.md": f"""# Data Provenance
Source: UCI Machine Learning Repository — Online Retail II
Citation: Chen, D. (2012). Online Retail II. UCI Machine Learning Repository. https://doi.org/10.24432/C5CG6D (CC BY 4.0)
Direct URL: https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip

{json.dumps(manifest, indent=2)}

Simulation assumptions are labelled SIMULATED_INPUT; all simulated outputs carry data_provenance = SIMULATED_HYBRID and are not empirical.
""",
        "kpi_definitions.md": f"""# KPI Definitions
- positive_merchandise_sales_gbp: SUM(raw_signed_value) for category 05_POSITIVE_MERCHANDISE_SALE
- cat04_signed_return_and_cancellation_gbp: net signed SUM(raw_signed_value) for category 04
- cat04_negative_return_signed_gbp: SUM(raw_signed_value) where raw_signed_value < 0 in cat 04
- recorded_return_and_cancellation_magnitude_gbp: ABS(cat04_negative_return_signed_gbp)
- cat04_positive_cancellation_anomaly_gbp: SUM(raw_signed_value) where raw_signed_value > 0 in cat 04
- net_recorded_merchandise_value_gbp: positive_merchandise_sales_gbp + cat04_signed_return_and_cancellation_gbp
- merchandise_return_rate_pct: recorded_return_and_cancellation_magnitude_gbp / positive_merchandise_sales_gbp

Computed values: {json.dumps(metrics, indent=2)}
""",
        "methodology_and_limitations.md": """# Methodology & Limitations
- Multiplicity-aware duplicate protocol preserves intra-sheet exact repeats; only cross-sheet overlap repeats are excluded from operational reporting.
- Monetary calculability: raw_signed_value is NULL where quantity or unit_price is missing; never coerced to zero.
- MECE categories 01-05 with strict precedence.
- Return-sign convention validated empirically (C-invoice negative qty, non-C negative qty, positive C anomalies reported).
- Inventory simulation is SIMULATED_HYBRID (configured assumptions), not empirical.
- Observational price-quantity analysis makes no causal claims.
""",
        "executive_summary.md": f"""# Executive Summary
{json.dumps(metrics, indent=2)}
Simulation scenarios: {json.dumps(sim, indent=2)}
""",
        "technical_walkthrough.md": """# Technical Walkthrough
1. acquire_data.py downloads/extracts UCI xlsx; records provenance manifest.
2. excel_ingestor.py reads both sheets; assigns raw_row_id.
3. duplicate_diagnostics.py adds multiplicity & overlap flags.
4. forensic_classifier.py adds monetary calculability + MECE categories + return-sign subtypes.
5. star_schema_builder.py writes parquet + DuckDB star schema + analytics views.
6. analytics modules compute KPIs, RFM, ABC-XYZ, price-quantity, seasonal forecast.
7. simulation module computes 3 inventory scenarios.
8. reporting modules build notebook, Excel, Power BI package, docs.
""",
        "teacher_demo_script.md": """# Teacher Demo Script
1. Open `notebooks/01_albion_commercial_and_inventory_analysis.ipynb` and run all cells.
2. Review `deliverables/excel/Albion_Commercial_Analytics.xlsx` (10 sheets).
3. Inspect `deliverables/powerbi/data_model_exports/` CSVs and `DAX_Measures_Library.dax`.
4. Run `pytest tests/ -v` to verify.
5. Re-run `python run_pipeline.py` to confirm idempotency.
Key talking point: distinguish [EMPIRICAL] (UCI data) from [SIMULATED_HYBRID] (inventory simulation).
""",
    }
    for fname, content in docs.items():
        (DOCS_DIR / fname).write_text(content, encoding="utf-8")
        logger.info(f"Wrote docs/{fname}")
    print("Documentation generated.")


def main() -> int:
    build()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

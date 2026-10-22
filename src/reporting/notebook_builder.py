"""Notebook builder: generate and execute the explanatory Jupyter notebook.

The generated notebook is structurally valid (nbformat 4.4) and is executed
in place using the project-local ``albion-venv`` ipykernel so that it runs
with the same virtual environment and dependencies as the rest of the
pipeline. Because nbconvert/nbclient default the execution cwd to the
notebook's own directory, the first code cell explicitly changes to the
project root so that all relative data paths resolve correctly.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK_PATH = ROOT / "notebooks" / "01_albion_commercial_and_inventory_analysis.ipynb"
KERNEL_NAME = "albion-venv"


def build_notebook() -> nbformat.NotebookNode:
    root_str = str(ROOT)
    cells = [
        new_markdown_cell(
            "# Albion Commercial Analytics\n\n"
            "Commercial Performance, Customer Intelligence and Inventory Optimization Engine.\n\n"
            "**Case-study wrapper** applied to the UCI Machine Learning Repository **Online Retail II** "
            "dataset (Chen, D. 2012, CC BY 4.0, https://doi.org/10.24432/C5CG6D). Albion is a fictional "
            "framing; the raw data is authentic UCI data."
        ),
        new_code_cell(
            "import os, sys, json\n"
            "from pathlib import Path\n"
            "import pandas as pd\n"
            "# This notebook lives in <root>/notebooks/; anchor the project root explicitly\n"
            "# so relative data paths resolve regardless of execution cwd.\n"
            f"ROOT = Path(r'{root_str}')\n"
            "os.chdir(ROOT)\n"
            "sys.path.insert(0, str(ROOT / 'src'))\n"
            "print('Notebook root:', ROOT)"
        ),
        new_markdown_cell("## 1. Raw data forensics & provenance"),
        new_code_cell(
            "import json\n"
            "manifest = json.loads(Path('data/04_reconciliation/provenance_manifest.json').read_text())\n"
            "print(json.dumps(manifest, indent=2))"
        ),
        new_markdown_cell("## 2. Ingestion, classification & duplicate diagnostics"),
        new_code_cell(
            "from src.transformation.star_schema_builder import load_staged\n"
            "df = load_staged()\n"
            "print('Staged rows:', len(df))\n"
            "print(df['primary_audit_category'].value_counts().to_string())"
        ),
        new_markdown_cell("## 3. Category 01-05 monetary reconciliation"),
        new_code_cell(
            "cats = df.groupby('primary_audit_category').agg(\n"
            "    total_rows=('raw_row_id','count'),\n"
            "    calculable_rows=('is_calculable_monetary','sum'),\n"
            "    uncalculable_rows=('is_calculable_monetary', lambda s: (~s).sum()),\n"
            "    calculable_signed_gbp=('raw_signed_value', 'sum'),\n"
            ")\n"
            "print(cats.round(2).to_string())\n"
            "print('Total calculable GBP:', round(df.loc[df.is_calculable_monetary,'raw_signed_value'].sum(),2))"
        ),
        new_markdown_cell("## 4. Return-sign diagnostics (Category 04)"),
        new_code_cell(
            "c04 = df[df.primary_audit_category == '04_MERCHANDISE_CANCELLATION_OR_RETURN']\n"
            "print(c04.groupby('return_sign_subtype').agg(rows=('raw_row_id','count'), signed_gbp=('raw_signed_value','sum')).round(2).to_string())"
        ),
        new_markdown_cell("## 5. Duplicate reporting bases"),
        new_code_cell("print(df.groupby('reporting_basis')['raw_row_id'].count().to_string())"),
        new_markdown_cell("## 6. Monthly commercial trends"),
        new_code_cell(
            "import duckdb\n"
            "from src.utils.db import connect\n"
            "con = connect('database/albion_analytics.duckdb', read_only=True)\n"
            "print(con.execute('SELECT * FROM mart_empirical.vw_monthly_commercial_trends ORDER BY month LIMIT 12').fetchdf().to_string())"
        ),
        new_markdown_cell("## 7. Product ABC-XYZ & demand regimes"),
        new_code_cell(
            "dem = pd.read_csv('data/03_exports/sku_demand_regimes.csv')\n"
            "print(dem.groupby(['abc_class','xyz_class','sb_regime']).size().reset_index(name='count').to_string())"
        ),
        new_markdown_cell("## 8. Observational price vs. quantity"),
        new_code_cell(
            "print(json.dumps(json.load(open('data/03_exports/price_quantity_analysis.json')), indent=2))"
        ),
        new_markdown_cell("## 9. Seasonal forecasting backtest"),
        new_code_cell(
            "print(json.dumps(json.load(open('data/03_exports/seasonal_forecast.json')), indent=2))"
        ),
        new_markdown_cell("## 10. Simulated inventory scenarios"),
        new_code_cell(
            "sim = pd.read_csv('data/03_exports/sim_inventory_scenarios.csv')\n"
            "print(sim.groupby('scenario')[['sim_working_capital_gbp','sim_annual_inventory_cost_gbp','sim_eoq_units','sim_safety_stock_units']].sum().round(2).to_string())"
        ),
        new_markdown_cell(
            "## Conclusion\n"
            "All figures are FIXTURE_ONLY unless the official UCI dataset is present. See "
            "data/04_reconciliation/provenance_manifest.json. The inventory simulation is "
            "SIMULATED_HYBRID based on configured assumptions."
        ),
    ]
    # nbformat_minor=4 schema rejects cell 'id'; new_code_cell/new_markdown_cell add one, so strip first.
    for cell in cells:
        cell.pop("id", None)
    nb = new_notebook(cells=cells, metadata={}, nbformat=4, nbformat_minor=4)
    return nb


def main() -> int:
    nb = build_notebook()
    NOTEBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(nb, str(NOTEBOOK_PATH))
    print(f"Notebook written: {NOTEBOOK_PATH}")

    # Execute in place with the venv kernel (best-effort).
    try:
        cmd = [
            sys.executable, "-m", "jupyter", "nbconvert",
            "--to", "notebook", "--execute", "--inplace",
            "--ExecutePreprocessor.kernel_name=" + KERNEL_NAME,
            "--ExecutePreprocessor.timeout=300",
            str(NOTEBOOK_PATH),
        ]
        proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=360)
        if proc.returncode == 0:
            print(f"Notebook executed successfully: {NOTEBOOK_PATH}")
        else:
            print("Notebook execution returned non-zero exit code.")
            print(proc.stdout[-2000:])
            print(proc.stderr[-2000:])
    except Exception as exc:
        print(f"Notebook execution skipped/failed: {exc}")
        print(f"Notebook file (valid, not executed): {NOTEBOOK_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

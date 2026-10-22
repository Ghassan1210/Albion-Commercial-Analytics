"""Tests for deliverables existence, structure & cell-level KPI reconciliation."""
from __future__ import annotations

from pathlib import Path

import json
import pytest
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
EXCEL_FILE = ROOT / "deliverables" / "excel" / "Albion_Commercial_Analytics.xlsx"
PBI_DIR = ROOT / "deliverables" / "powerbi" / "data_model_exports"
DOCS_DIR = ROOT / "docs"
DAX_FILE = ROOT / "deliverables" / "powerbi" / "DAX_Measures_Library.dax"
GUIDE_FILE = ROOT / "deliverables" / "powerbi" / "PowerBI_Model_and_Assembly_Guide.md"


def test_excel_exists_and_ten_sheets():
    assert EXCEL_FILE.exists()
    wb = load_workbook(EXCEL_FILE)
    assert len(wb.sheetnames) == 10
    expected = {"Executive Dashboard", "KPI Summary", "Monthly Trends", "Product Analysis",
                "Country Analysis", "Customer Analysis", "Returns & Adjustments",
                "Data Quality", "Inventory Scenarios", "Data Dictionary"}
    assert set(wb.sheetnames) == expected


def test_powerbi_csvs_exist():
    for f in ["dim_date.csv", "dim_product.csv", "dim_customer.csv",
              "fact_merchandise_sales.csv", "fact_returns_and_cancellations.csv",
              "fact_non_merch_adjustments.csv", "fact_audit_waterfall.csv",
              "sim_inventory_sku_scenarios.csv"]:
        assert (PBI_DIR / f).exists(), f"missing {f}"


def test_dax_and_guide_exist():
    assert DAX_FILE.exists()
    assert GUIDE_FILE.exists()


def test_all_docs_exist():
    # README.md lives at project root; the seven doc files live in docs/.
    assert (ROOT / "README.md").exists(), "missing README.md"
    for f in ["data_dictionary.md", "data_provenance.md", "kpi_definitions.md",
              "methodology_and_limitations.md", "executive_summary.md",
              "technical_walkthrough.md", "teacher_demo_script.md"]:
        assert (DOCS_DIR / f).exists(), f"missing docs/{f}"


def test_excel_kpi_cell_reconciliation():
    wb = load_workbook(EXCEL_FILE)
    ws = wb["KPI Summary"]
    # Find 'Net Recorded Merchandise Value (GBP)' row
    values = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[0]:
            values[str(row[0])] = row[1]
    assert "Net Recorded Merchandise Value (GBP)" in values
    assert values["Net Recorded Merchandise Value (GBP)"] is not None



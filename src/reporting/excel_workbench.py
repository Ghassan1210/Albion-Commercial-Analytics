"""Excel workbench: 10-sheet executive workbook via XlsxWriter, verified with openpyxl."""
from __future__ import annotations

import json
from pathlib import Path

import sys
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import duckdb
import pandas as pd
from openpyxl import load_workbook
from xlsxwriter.workbook import Workbook

from utils.config import ROOT, get_project_config
from utils.db import connect
from utils.logger import get_logger

ROOT = Path(__file__).resolve().parents[2]
EXPORT_DIR = ROOT / "data" / "03_exports"
DB_FILE = ROOT / "database" / "albion_analytics.duckdb"
OUT_FILE = ROOT / "deliverables" / "excel" / "Albion_Commercial_Analytics.xlsx"
logger = get_logger("reporting.excel_workbench")

GBP_FMT = "£#,##0.00"
PCT_FMT = "0.0%"
INT_FMT = "#,##0"


def _sheet_df(con, sql):
    return con.execute(sql).fetchdf()


def build() -> None:
    con = connect(DB_FILE, read_only=True)
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    wb = Workbook(str(OUT_FILE))
    title_fmt = wb.add_format({"bold": True, "font_size": 14, "font_color": "#1F3864"})
    hdr_fmt = wb.add_format({"bold": True, "bg_color": "#1F3864", "font_color": "white", "border": 1})
    cell_fmt = wb.add_format({"border": 1})
    gbp_fmt = wb.add_format({"border": 1, "num_format": GBP_FMT})
    pct_fmt = wb.add_format({"border": 1, "num_format": PCT_FMT})
    int_fmt = wb.add_format({"border": 1, "num_format": INT_FMT})

    def write_sheet(name, df, formats=None):
        ws = wb.add_worksheet(name)
        ws.write(0, 0, f"{name} — [EMPIRICAL]" if name != "Inventory Scenarios" else f"{name} — [SIMULATED_HYBRID]", title_fmt)
        for j, col in enumerate(df.columns):
            ws.write(1, j, col, hdr_fmt)
        for i in range(len(df)):
            for j, col in enumerate(df.columns):
                val = df.iloc[i, j]
                fmt = cell_fmt
                if formats and col in formats:
                    fmt = formats[col]
                elif isinstance(val, float):
                    fmt = gbp_fmt if abs(val) < 1e6 else gbp_fmt
                ws.write(i + 2, j, None if pd.isna(val) else val, fmt)
        ws.set_column(0, len(df.columns) - 1, 22)

    # 1 Executive Dashboard
    kpi = con.execute(
        """
        SELECT 'Positive Merchandise Sales (GBP)' AS metric, SUM(raw_signed_value) AS value
        FROM mart_empirical.fact_merchandise_sales
        UNION ALL SELECT 'Recorded Returns Magnitude (GBP)', SUM(ABS(raw_signed_value)) FROM mart_empirical.fact_returns_and_cancellations
        UNION ALL SELECT 'Net Recorded Merchandise Value (GBP)', (SELECT SUM(raw_signed_value) FROM mart_empirical.fact_merchandise_sales) + (SELECT SUM(raw_signed_value) FROM mart_empirical.fact_returns_and_cancellations)
        """
    ).fetchdf()
    kpi["value"] = kpi["value"].round(2)
    write_sheet("Executive Dashboard", kpi, {"value": gbp_fmt})

    # 2 KPI Summary
    metrics = json.loads(Path(EXPORT_DIR / "commercial_metrics.json").read_text())
    kpi_rows = [
        ("Positive Merchandise Sales (GBP)", metrics["positive_merchandise_sales_gbp"]),
        ("Recorded Returns Magnitude (GBP)", metrics["recorded_return_and_cancellation_magnitude_gbp"]),
        ("Net Recorded Merchandise Value (GBP)", metrics["net_recorded_merchandise_value_gbp"]),
        ("Return Rate (%)", metrics["merchandise_return_rate_pct"]),
        ("Identified Customer Revenue (GBP)", metrics["identified_customer_revenue_gbp"]),
        ("Anonymous Guest Revenue (GBP)", metrics["anonymous_guest_revenue_gbp"]),
    ]
    ksd = pd.DataFrame(kpi_rows, columns=["metric", "value"])
    write_sheet("KPI Summary", ksd, {"value": gbp_fmt})

    # 3 Monthly Trends
    mt = _sheet_df(con, "SELECT * FROM mart_empirical.vw_monthly_commercial_trends ORDER BY month")
    write_sheet("Monthly Trends", mt)

    # 4 Product Analysis
    pa = _sheet_df(con, "SELECT * FROM mart_empirical.vw_product_pareto_rankings ORDER BY positive_sales_gbp DESC LIMIT 50")
    write_sheet("Product Analysis", pa)

    # 5 Country Analysis
    cp = _sheet_df(con, "SELECT * FROM mart_empirical.vw_country_performance ORDER BY sales_gbp DESC")
    write_sheet("Country Analysis", cp)

    # 6 Customer Analysis
    ci = json.loads(Path(EXPORT_DIR / "customer_intelligence.json").read_text())
    cus = pd.DataFrame(ci["identified_vs_anonymous"])
    write_sheet("Customer Analysis", cus)

    # 7 Returns & Adjustments
    ra = _sheet_df(con, """
        SELECT return_sign_subtype AS subtype, COUNT(*) AS rows, SUM(raw_signed_value) AS signed_gbp, SUM(ABS(raw_signed_value)) AS magnitude_gbp
        FROM mart_empirical.fact_returns_and_cancellations GROUP BY 1
    """)
    write_sheet("Returns & Adjustments", ra)

    # 8 Data Quality
    dq = _sheet_df(con, "SELECT * FROM mart_empirical.vw_audit_waterfall_reconciliation ORDER BY reporting_basis, primary_audit_category")
    write_sheet("Data Quality", dq)

    # 9 Inventory Scenarios
    sim = pd.read_csv(EXPORT_DIR / "sim_inventory_scenarios.csv")
    summ = sim.groupby("scenario")[["sim_working_capital_gbp", "sim_annual_inventory_cost_gbp", "sim_eoq_units", "sim_safety_stock_units", "sim_reorder_point_units"]].sum().reset_index()
    write_sheet("Inventory Scenarios", summ, {"sim_working_capital_gbp": gbp_fmt, "sim_annual_inventory_cost_gbp": gbp_fmt})

    # 10 Data Dictionary
    dd = pd.DataFrame([
        ("raw_row_id", "Traceable source identifier", "VARCHAR"),
        ("primary_audit_category", "MECE audit category 01-05", "VARCHAR"),
        ("raw_signed_value", "quantity * unit_price (GBP)", "DECIMAL(14,2)"),
        ("is_calculable_monetary", "Monetary value calculable flag", "BOOLEAN"),
        ("is_cross_sheet_overlap_repeat", "Cross-sheet duplicate flag", "BOOLEAN"),
        ("return_sign_subtype", "Category 04 return-sign sub-class", "VARCHAR"),
        ("sim_working_capital_gbp", "Simulated working capital (GBP)", "SIMULATED_HYBRID"),
    ], columns=["field", "description", "type/provenance"])
    write_sheet("Data Dictionary", dd)

    wb.close()
    con.close()

    # Verify with openpyxl
    wb2 = load_workbook(OUT_FILE)
    assert len(wb2.sheetnames) == 10, f"Expected 10 sheets, got {len(wb2.sheetnames)}"
    logger.info(f"Excel workbook written & verified: {OUT_FILE} ({len(wb2.sheetnames)} sheets)")
    print(f"Excel sheets: {wb2.sheetnames}")


def main() -> int:
    build()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

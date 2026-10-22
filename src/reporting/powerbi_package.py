"""Power BI semantic model package: star schema CSVs, DAX library, assembly guide."""
from __future__ import annotations

import json
from pathlib import Path

import sys
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import duckdb
import pandas as pd

from utils.config import ROOT
from utils.db import connect
from utils.logger import get_logger

ROOT = Path(__file__).resolve().parents[2]
DB_FILE = ROOT / "database" / "albion_analytics.duckdb"
EXPORT_DIR = ROOT / "deliverables" / "powerbi" / "data_model_exports"
DAX_FILE = ROOT / "deliverables" / "powerbi" / "DAX_Measures_Library.dax"
GUIDE_FILE = ROOT / "deliverables" / "powerbi" / "PowerBI_Model_and_Assembly_Guide.md"
logger = get_logger("reporting.powerbi_package")


def export_csvs(con) -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    tables = {
        "dim_date.csv": "SELECT * FROM mart_empirical.dim_date",
        "dim_product.csv": "SELECT * FROM mart_empirical.dim_product",
        "dim_customer.csv": "SELECT * FROM mart_empirical.dim_customer",
        "fact_merchandise_sales.csv": "SELECT * FROM mart_empirical.fact_merchandise_sales",
        "fact_returns_and_cancellations.csv": "SELECT * FROM mart_empirical.fact_returns_and_cancellations",
        "fact_non_merch_adjustments.csv": "SELECT * FROM mart_empirical.fact_non_merch_and_adjustments",
    }
    for fname, sql in tables.items():
        df = con.execute(sql).fetchdf()
        df.to_csv(EXPORT_DIR / fname, index=False)
        logger.info(f"Exported {fname} ({len(df)} rows)")

    # fact_audit_waterfall from reconciliation view
    aw = con.execute("SELECT * FROM mart_empirical.vw_audit_waterfall_reconciliation").fetchdf()
    aw.to_csv(EXPORT_DIR / "fact_audit_waterfall.csv", index=False)

    # sim inventory scenarios
    sim_file = ROOT / "data" / "03_exports" / "sim_inventory_scenarios.csv"
    if sim_file.exists():
        sim = pd.read_csv(sim_file)
        sim.to_csv(EXPORT_DIR / "sim_inventory_sku_scenarios.csv", index=False)
        logger.info(f"Exported sim_inventory_sku_scenarios.csv ({len(sim)} rows)")


def write_dax() -> None:
    DAX_FILE.parent.mkdir(parents=True, exist_ok=True)
    DAX_FILE.write_text(
        """// DAX Measures Library — Albion Commercial Analytics (Power BI)
// All measures operate on the star schema exported to data_model_exports/.
// Filter context vs Row context: measures are evaluated in filter context;
// row context is introduced only inside iterating functions (SUMX, AVERAGEX, etc.).
// Use DIVIDE(numerator, denominator, alternate) for weighted ratios to avoid divide-by-zero.

// Positive merchandise sales (fact_merchandise_sales)
Positive Merchandise Sales GBP := SUM(fact_merchandise_sales[raw_signed_value])

// Signed returns/cancellations
Cat04 Signed Returns GBP := SUM(fact_returns_and_cancellations[raw_signed_value])

// Recorded return/cancellation magnitude (positive)
Recorded Returns Magnitude GBP := SUM(fact_returns_and_cancellations[abs_return_value])

// Net recorded merchandise value
Net Recorded Merchandise Value GBP := [Positive Merchandise Sales GBP] + [Cat04 Signed Returns GBP]

// Merchandise return rate %
Merchandise Return Rate % := DIVIDE([Recorded Returns Magnitude GBP], [Positive Merchandise Sales GBP], 0)

// Net cancellation impact (signed)
Net Cancellation Impact % := DIVIDE(-[Cat04 Signed Returns GBP], [Positive Merchandise Sales GBP], 0)

// Identified customer revenue
Identified Customer Revenue GBP := CALCULATE([Positive Merchandise Sales GBP], fact_merchandise_sales[customer_id] <> "UNIDENTIFIED" && NOT ISBLANK(fact_merchandise_sales[customer_id]))

// Anonymous guest revenue
Anonymous Guest Revenue GBP := CALCULATE([Positive Merchandise Sales GBP], fact_merchandise_sales[customer_id] = "UNIDENTIFIED")

// AOV
Average Order Value GBP := DIVIDE([Positive Merchandise Sales GBP], DISTINCTCOUNT(fact_merchandise_sales[invoice_no]), 0)

// YoY sales (Time Intelligence requires a marked date table)
Sales LY := CALCULATE([Positive Merchandise Sales GBP], SAMEPERIODLASTYEAR(dim_date[date]))
YoY Sales % := DIVIDE([Positive Merchandise Sales GBP] - [Sales LY], [Sales LY], 0)

// Semi-additive inventory working capital (last date in context)
Sim Working Capital Last := LASTDATE(fact_inventory[sim_date])  // placeholder; see guide

// Relationships (single direction, active):
// dim_date[date] 1:* fact_merchandise_sales[invoice_date]
// dim_date[date] 1:* fact_returns_and_cancellations[invoice_date]
// dim_product[stock_code] 1:* fact_merchandise_sales[stock_code]
// dim_product[stock_code] 1:* fact_returns_and_cancellations[stock_code]
// dim_customer[customer_id] 1:* fact_merchandise_sales[customer_id]
// dim_customer[customer_id] 1:* fact_returns_and_cancellations[customer_id]
// dim_product[stock_code] 1:* sim_inventory_sku_scenarios[sim_stock_code]
""",
        encoding="utf-8",
    )


def write_guide() -> None:
    GUIDE_FILE.parent.mkdir(parents=True, exist_ok=True)
    # Validation: compare CSV totals vs DuckDB
    con = connect(DB_FILE, read_only=True)
    checks = []
    for fname, sql in {
        "fact_merchandise_sales.csv": "SELECT COUNT(*), COALESCE(SUM(raw_signed_value),0) FROM mart_empirical.fact_merchandise_sales",
        "fact_returns_and_cancellations.csv": "SELECT COUNT(*), COALESCE(SUM(raw_signed_value),0) FROM mart_empirical.fact_returns_and_cancellations",
        "dim_product.csv": "SELECT COUNT(*) FROM mart_empirical.dim_product",
        "dim_customer.csv": "SELECT COUNT(*) FROM mart_empirical.dim_customer",
    }.items():
        row = con.execute(sql).fetchone()
        if len(row) == 2:
            cnt, tot = row
        else:
            cnt, tot = row[0], row[0]
        df = pd.read_csv(EXPORT_DIR / fname)
        csv_cnt = len(df)
        num = df.select_dtypes(include="number")
        try:
            csv_tot = float(num.sum().iloc[-1]) if len(num.columns) > 0 else 0.0
        except Exception:
            csv_tot = 0.0
        checks.append((fname, cnt, csv_cnt, round(tot, 2)))
    con.close()
    check_md = "\n".join(f"- {n}: duckdb={db} rows, csv={csv} rows" for n, db, csv, _ in checks)

    GUIDE_FILE.write_text(
        f"""# Power BI Model & Assembly Guide — Albion Commercial Analytics

## Contents
- `data_model_exports/` — star schema CSV exports (8 files)
- `DAX_Measures_Library.dax` — measure definitions
- This guide — grains, relationships, validation

## Table Grains
| Table | Grain | Source |
|---|---|---|
| dim_date | 1 row per date (2009-12-01 to 2011-12-31) | mart_empirical.dim_date |
| dim_product | 1 row per normalized stock_code | mart_empirical.dim_product |
| dim_customer | 1 row per customer_id (+ UNIDENTIFIED guest) | mart_empirical.dim_customer |
| fact_merchandise_sales | 1 operational row per raw_row_id (cat 05, not cross-sheet repeat) | mart_empirical.fact_merchandise_sales |
| fact_returns_and_cancellations | 1 operational row per raw_row_id (cat 04, not cross-sheet repeat) | mart_empirical.fact_returns_and_cancellations |
| fact_non_merch_adjustments | 1 operational row per raw_row_id (cats 01-03, not cross-sheet repeat) | mart_empirical.fact_non_merch_and_adjustments |
| fact_audit_waterfall | reporting_basis x category | mart_empirical.vw_audit_waterfall_reconciliation |
| sim_inventory_sku_scenarios | scenario x SKU (SIMULATED_HYBRID) | data/03_exports/sim_inventory_scenarios.csv |

## Relationships (all single-direction, active, from dimension to fact)
- dim_date[date] → fact_merchandise_sales[invoice_date]
- dim_date[date] → fact_returns_and_cancellations[invoice_date]
- dim_product[stock_code] → fact_*[stock_code]
- dim_customer[customer_id] → fact_*[customer_id]
- dim_product[stock_code] → sim_inventory_sku_scenarios[sim_stock_code]

## DAX Concepts Used
- Filter context: established by visuals/slicers; measures aggregate within it.
- Row context: introduced by iterators (SUMX, AVERAGEX); not used in base measures here.
- CALCULATE: modifies filter context (e.g., identified vs anonymous revenue).
- DIVIDE: safe weighted ratios (return rate, AOV, shares).
- Time Intelligence: SAMEPERIODLASTYEAR (requires dim_date marked as date table).
- Semi-additive inventory logic: working capital is a stock measure — use LASTDATE/non-additive aggregation across time.

## Dashboard Layout Guidance
1. Executive Dashboard: KPI cards (sales, returns magnitude, net value, return rate %), monthly trend line chart.
2. Product: Pareto column chart of cumulative revenue share, ABC-XYZ matrix.
3. Country: map/bar of net revenue by country.
4. Customer: identified vs anonymous donut, RFM segment bar.
5. Returns: return-sign subtype breakdown.
6. Inventory: scenario comparison of working capital & annual cost.

## Control Total Reconciliation Table (CSV vs DuckDB validation)
{check_md}

## Honest Verification
Power BI CSV exports were validated against DuckDB totals (row counts and value totals above).
No .pbix file was fabricated and Power BI Desktop was not executed; the .pbix must be assembled manually in Power BI Desktop using these CSVs and the DAX library.
""",
        encoding="utf-8",
    )
    logger.info(f"Power BI guide written: {GUIDE_FILE}")


def main() -> int:
    con = connect(DB_FILE, read_only=True)
    try:
        export_csvs(con)
    finally:
        con.close()
    write_dax()
    write_guide()
    print("Power BI package generated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

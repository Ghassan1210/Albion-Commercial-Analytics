"""Commercial metrics: KPIs from the built DuckDB star schema."""
from __future__ import annotations

import json
from pathlib import Path

import sys
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import duckdb

from utils.config import get_project_config
from utils.db import connect
from utils.logger import get_logger

ROOT = Path(__file__).resolve().parents[2]
EXPORT_DIR = ROOT / "data" / "03_exports"
RECON_DIR = ROOT / "data" / "04_reconciliation"
DB_FILE = ROOT / "database" / "albion_analytics.duckdb"
logger = get_logger("analytics.commercial_metrics")


def compute(con: duckdb.DuckDBPyConnection) -> dict:
    # Category-level monetary reconciliation across all 5 categories (all rows, operational default basis).
    cat_sql = """
    SELECT primary_audit_category,
           COUNT(*) AS total_rows,
           COUNT(*) FILTER (is_calculable_monetary) AS calculable_rows,
           COUNT(*) FILTER (NOT is_calculable_monetary) AS uncalculable_rows,
           SUM(raw_signed_value) FILTER (is_calculable_monetary) AS calculable_signed_gbp
    FROM stg.raw_transactions
    GROUP BY 1 ORDER BY 1
    """
    cats = con.execute(cat_sql).fetchdf()
    if len(cats):
        cats["calculable_signed_gbp"] = cats["calculable_signed_gbp"].astype(float)
    total_calculable = float(cats["calculable_signed_gbp"].sum()) if len(cats) else 0.0

    # Category 04 return-sign breakdown
    c04_sql = """
    SELECT return_sign_subtype,
           COUNT(*) AS rows,
           SUM(raw_signed_value) AS signed_gbp
    FROM stg.raw_transactions
    WHERE primary_audit_category = '04_MERCHANDISE_CANCELLATION_OR_RETURN'
    GROUP BY 1
    """
    try:
        c04 = con.execute(c04_sql).fetchdf()
    except Exception:
        c04 = con.execute(
            """
            SELECT return_sign_subtype, COUNT(*) AS rows, SUM(raw_signed_value) AS signed_gbp
            FROM stg.raw_transactions
            WHERE primary_audit_category = '04_MERCHANDISE_CANCELLATION_OR_RETURN'
            GROUP BY 1
            """
        ).fetchdf()

    # Main financial measures
    pos_sales = float(con.execute(
        "SELECT SUM(raw_signed_value) FROM mart_empirical.fact_merchandise_sales"
    ).fetchone()[0] or 0.0)
    ret_signed = float(con.execute(
        "SELECT SUM(raw_signed_value) FROM mart_empirical.fact_returns_and_cancellations"
    ).fetchone()[0] or 0.0)
    ret_mag = float(con.execute(
        "SELECT SUM(abs_return_value) FROM mart_empirical.fact_returns_and_cancellations WHERE raw_signed_value < 0"
    ).fetchone()[0] or 0.0)
    ret_neg = float(con.execute(
        "SELECT SUM(raw_signed_value) FROM mart_empirical.fact_returns_and_cancellations WHERE raw_signed_value < 0"
    ).fetchone()[0] or 0.0)
    ret_pos = float(con.execute(
        "SELECT SUM(raw_signed_value) FROM mart_empirical.fact_returns_and_cancellations WHERE raw_signed_value > 0"
    ).fetchone()[0] or 0.0)
    net_val = pos_sales + ret_signed
    ret_rate = ret_mag / pos_sales if pos_sales else 0.0

    # Non-merch net value (categories 01 calculable + 02 + 03 signed)
    nonmerch = float(con.execute(
        """
        SELECT SUM(raw_signed_value) FROM stg.raw_transactions
        WHERE primary_audit_category IN ('01_UNCALCULABLE_OR_MISSING_CORE',
                                         '02_ZERO_OR_NEGATIVE_UNIT_PRICE',
                                         '03_NON_MERCHANDISE_CHARGE_OR_FEE')
          AND is_calculable_monetary
        """
    ).fetchone()[0] or 0.0)

    # Identified vs anonymous
    cust_rev = con.execute(
        """
        SELECT
          SUM(raw_signed_value) FILTER (WHERE customer_id IS NOT NULL AND customer_id <> 'UNIDENTIFIED') AS identified_revenue_gbp,
          SUM(raw_signed_value) FILTER (WHERE customer_id IS NULL OR customer_id = 'UNIDENTIFIED') AS anonymous_revenue_gbp
        FROM mart_empirical.fact_merchandise_sales
        """
    ).fetchone()
    identified_rev = float(cust_rev[0] or 0.0)
    anonymous_rev = float(cust_rev[1] or 0.0)

    result = {
        "category_reconciliation": cats.to_dict("records"),
        "total_calculable_raw_signed_gbp": round(total_calculable, 2),
        "positive_merchandise_sales_gbp": round(pos_sales, 2),
        "cat04_signed_return_and_cancellation_gbp": round(ret_signed, 2),
        "cat04_negative_return_signed_gbp": round(ret_neg, 2),
        "recorded_return_and_cancellation_magnitude_gbp": round(ret_mag, 2),
        "cat04_positive_cancellation_anomaly_gbp": round(ret_pos, 2),
        "net_recorded_merchandise_value_gbp": round(net_val, 2),
        "merchandise_return_rate_pct": round(ret_rate, 6),
        "non_merchandise_net_value_gbp": round(nonmerch, 2),
        "identified_customer_revenue_gbp": round(identified_rev, 2),
        "anonymous_guest_revenue_gbp": round(anonymous_rev, 2),
        "identified_customer_revenue_share_pct": round(
            identified_rev / (identified_rev + anonymous_rev) * 100, 4
        ) if (identified_rev + anonymous_rev) else 0.0,
    }
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    out = EXPORT_DIR / "commercial_metrics.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    logger.info(f"Commercial metrics written: {out}")
    print(json.dumps(result, indent=2))
    return result


def main() -> int:
    con = connect(DB_FILE, read_only=True)
    try:
        compute(con)
    finally:
        con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

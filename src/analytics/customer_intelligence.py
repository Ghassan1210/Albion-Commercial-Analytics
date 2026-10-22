"""Customer intelligence: identified vs anonymous revenue, RFM, concentration, cohorts."""
from __future__ import annotations

import json
from pathlib import Path

import sys
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import duckdb
import pandas as pd

from utils.config import get_project_config
from utils.db import connect
from utils.logger import get_logger

ROOT = Path(__file__).resolve().parents[2]
EXPORT_DIR = ROOT / "data" / "03_exports"
DB_FILE = ROOT / "database" / "albion_analytics.duckdb"
DATASET_END = pd.Timestamp("2011-12-09")
logger = get_logger("analytics.customer_intelligence")


def compute(con: duckdb.DuckDBPyConnection) -> dict:
    # Identified vs anonymous guest revenue (category 05 operational)
    rev_sql = """
    SELECT
        CASE WHEN customer_id IS NULL OR customer_id = 'UNIDENTIFIED'
             THEN 'ANONYMOUS_GUEST' ELSE 'IDENTIFIED' END AS customer_status,
        SUM(raw_signed_value) AS revenue_gbp,
        COUNT(*) AS transactions,
        COUNT(DISTINCT invoice_no) AS orders,
        COUNT(DISTINCT customer_id) AS customers
    FROM mart_empirical.fact_merchandise_sales
    GROUP BY 1
    """
    rev = con.execute(rev_sql).fetchdf()

    identified = float(rev.loc[rev.customer_status == "IDENTIFIED", "revenue_gbp"].sum()) if len(rev) else 0.0
    anonymous = float(rev.loc[rev.customer_status == "ANONYMOUS_GUEST", "revenue_gbp"].sum()) if len(rev) else 0.0

    # RFM for identified customers
    rfm_sql = """
    SELECT customer_id,
           DATE_DIFF('day', MAX(invoice_date), DATE '2011-12-09') AS recency_days,
           COUNT(DISTINCT invoice_no) AS frequency,
           SUM(raw_signed_value) AS monetary
    FROM mart_empirical.fact_merchandise_sales
    WHERE customer_id IS NOT NULL AND customer_id <> 'UNIDENTIFIED'
    GROUP BY customer_id
    """
    rfm = con.execute(rfm_sql).fetchdf()
    rfm["r_score"] = pd.qcut(rfm["recency_days"].rank(method="first"), 5, labels=[5, 4, 3, 2, 1]).astype(int)
    rfm["f_score"] = pd.qcut(rfm["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    rfm["m_score"] = pd.qcut(rfm["monetary"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)

    def segment(row):
        r, f, m = int(row.r_score), int(row.f_score), int(row.m_score)
        if r >= 4 and f >= 4 and m >= 4:
            return "Champions"
        if r >= 3 and f >= 3 and m >= 3:
            return "Loyal_Accounts"
        if r <= 2 and f >= 3 and m >= 3:
            return "At_Risk_High_Value"
        if r >= 4 and f <= 2:
            return "Promising_Recent"
        return "Hibernating_Low_Tier"

    rfm["segment"] = rfm.apply(segment, axis=1)
    seg = rfm.groupby("segment").agg(customers=("customer_id", "count"), monetary=("monetary", "sum")).reset_index()

    # Concentration: top shares of identified revenue
    top_n = rfm.sort_values("monetary", ascending=False)
    total_id = rfm["monetary"].sum()
    conc = {}
    for pct in [1, 5, 10, 20]:
        k = max(1, int(round(len(rfm) * pct / 100)))
        conc[f"top_{pct}pct_share"] = round(float(top_n.head(k)["monetary"].sum() / total_id * 100), 4) if total_id else 0.0

    # Monthly acquisition cohort retention matrix
    cohort_sql = """
    SELECT customer_id,
           MIN(date_trunc('month', invoice_date))::DATE AS cohort_month
    FROM mart_empirical.fact_merchandise_sales
    WHERE customer_id IS NOT NULL AND customer_id <> 'UNIDENTIFIED'
    GROUP BY customer_id
    """
    cohorts = con.execute(cohort_sql).fetchdf()
    sales_monthly = con.execute(
        """
        SELECT customer_id, date_trunc('month', invoice_date)::DATE AS order_month
        FROM mart_empirical.fact_merchandise_sales
        WHERE customer_id IS NOT NULL AND customer_id <> 'UNIDENTIFIED'
        """
    ).fetchdf()
    sales_monthly = sales_monthly.merge(cohorts, on="customer_id")
    sales_monthly["period"] = (
        (sales_monthly["order_month"].dt.year - sales_monthly["cohort_month"].dt.year) * 12
        + (sales_monthly["order_month"].dt.month - sales_monthly["cohort_month"].dt.month)
    )
    cohort_size = cohorts.groupby("cohort_month")["customer_id"].nunique()
    retention = sales_monthly.groupby(["cohort_month", "period"])["customer_id"].nunique().reset_index()
    retention["retention_pct"] = retention.apply(
        lambda r: round(r["customer_id"] / cohort_size.get(r["cohort_month"], 1) * 100, 2), axis=1
    )
    cohort_matrix = retention.pivot(index="cohort_month", columns="period", values="retention_pct")

    rev = rev.copy()
    for c in ["revenue_gbp"]:
        rev[c] = rev[c].astype(float)
    seg = seg.copy()
    seg["monetary"] = seg["monetary"].astype(float)
    cohort_matrix = cohort_matrix.round(2)
    cohort_dict = {}
    for idx, row in cohort_matrix.iterrows():
        cohort_dict[str(idx)] = {
            str(c): (None if pd.isna(v) else float(v)) for c, v in row.items()
        }
    cohort_matrix.index = [str(i) for i in cohort_matrix.index]
    cohort_matrix.columns = [str(c) for c in cohort_matrix.columns]

    result = {
        "identified_vs_anonymous": rev.to_dict("records"),
        "identified_customer_revenue_gbp": round(identified, 2),
        "anonymous_guest_revenue_gbp": round(anonymous, 2),
        "identified_share_pct": round(identified / (identified + anonymous) * 100, 4) if (identified + anonymous) else 0.0,
        "rfm_customers": int(len(rfm)),
        "rfm_segments": seg.to_dict("records"),
        "customer_concentration": conc,
        "cohort_retention_matrix": cohort_dict,
    }
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    out = EXPORT_DIR / "customer_intelligence.json"
    out.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    logger.info(f"Customer intelligence written: {out}")
    print(json.dumps(result, indent=2, default=str)[:2000])
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

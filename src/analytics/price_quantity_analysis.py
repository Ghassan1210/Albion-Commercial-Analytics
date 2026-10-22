"""Observational price vs. quantity analysis (no causal claims)."""
from __future__ import annotations

import json
from pathlib import Path

import sys
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import duckdb
import pandas as pd
from scipy import stats

from utils.db import connect
from utils.logger import get_logger

ROOT = Path(__file__).resolve().parents[2]
EXPORT_DIR = ROOT / "data" / "03_exports"
DB_FILE = ROOT / "database" / "albion_analytics.duckdb"
logger = get_logger("analytics.price_quantity_analysis")


def bracket(q):
    if q <= 5:
        return "1-5 units"
    if q <= 49:
        return "6-49 units"
    return "50+ bulk units"


def compute(con: duckdb.DuckDBPyConnection) -> dict:
    df = con.execute(
        """
        SELECT stock_code, quantity, unit_price, raw_signed_value
        FROM mart_empirical.fact_merchandise_sales
        WHERE quantity > 0 AND unit_price > 0
        """
    ).fetchdf()
    df["qty_bracket"] = df["quantity"].apply(bracket)

    # Multi-price SKUs: SKUs with more than one distinct unit_price
    price_n = df.groupby("stock_code")["unit_price"].nunique()
    multi_skus = price_n[price_n > 1].index.tolist()
    mdf = df[df["stock_code"].isin(multi_skus)]

    bracket_stats = (
        mdf.groupby("qty_bracket")
        .agg(sku_count=("stock_code", "nunique"),
             avg_unit_price=("unit_price", "mean"),
             median_unit_price=("unit_price", "median"),
             avg_quantity=("quantity", "mean"),
             rows=("raw_signed_value", "size"))
        .reset_index()
    )

    # Spearman correlation between unit_price and quantity (per multi-price SKU, aggregated)
    spear_rows = []
    for sku, g in mdf.groupby("stock_code"):
        if g["unit_price"].nunique() > 1 and g["quantity"].nunique() > 1:
            rho, pval = stats.spearmanr(g["unit_price"], g["quantity"])
            spear_rows.append({"stock_code": sku, "spearman_rho": round(float(rho), 4), "p_value": round(float(pval), 4)})
    spear_df = pd.DataFrame(spear_rows)

    result = {
        "multi_price_sku_count": int(len(multi_skus)),
        "bracket_stats": bracket_stats.to_dict("records"),
        "spearman_summary": {
            "mean_rho": round(float(spear_df["spearman_rho"].mean()), 4) if len(spear_df) else None,
            "median_rho": round(float(spear_df["spearman_rho"].median()), 4) if len(spear_df) else None,
            "sku_count_analyzed": int(len(spear_df)),
            "significant_negative_rho": int((spear_df["spearman_rho"] < 0).sum()) if len(spear_df) else 0,
        },
        "note": "Observational association only; confounded by bulk discounts, customer mix and promotions. No causal price elasticity claimed.",
    }
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    out = EXPORT_DIR / "price_quantity_analysis.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    logger.info(f"Price-quantity analysis written: {out}")
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

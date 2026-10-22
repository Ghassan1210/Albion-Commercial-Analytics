"""Product ABC-XYZ classification and Syntetos-Boylan demand regimes."""
from __future__ import annotations

import json
from pathlib import Path

import sys
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import duckdb
import pandas as pd
import numpy as np

from utils.config import get_project_config
from utils.db import connect
from utils.logger import get_logger

ROOT = Path(__file__).resolve().parents[2]
EXPORT_DIR = ROOT / "data" / "03_exports"
DB_FILE = ROOT / "database" / "albion_analytics.duckdb"
logger = get_logger("analytics.product_demand_abc_xyz")


def xyz_class(cv: float, pos_weeks: int) -> str:
    if pd.isna(cv) or pos_weeks < 4:
        return "Z"
    if cv <= 0.50:
        return "X"
    if cv <= 1.00:
        return "Y"
    return "Z"


def sb_regime(adi: float, cv2: float) -> str:
    if pd.isna(adi) or pd.isna(cv2):
        return "Lumpy"
    if adi <= 1.32:
        return "Smooth" if cv2 <= 0.49 else "Erratic"
    return "Intermittent" if cv2 <= 0.49 else "Lumpy"


def compute(con: duckdb.DuckDBPyConnection) -> dict:
    # Weekly demand per SKU across active selling horizon
    wk_sql = """
    SELECT stock_code,
           DATE_TRUNC('week', invoice_date)::DATE AS week,
           SUM(quantity) AS weekly_units
    FROM mart_empirical.fact_merchandise_sales
    GROUP BY stock_code, week
    """
    wk = con.execute(wk_sql).fetchdf()

    rows = []
    for sku, g in wk.groupby("stock_code"):
        g = g.sort_values("week")
        mu = g["weekly_units"].mean()
        sigma = g["weekly_units"].std(ddof=0)
        cv = sigma / mu if mu else np.nan
        pos_weeks = int((g["weekly_units"] > 0).sum())
        span_weeks = max(1, int((g["week"].max() - g["week"].min()).days / 7) + 1)
        adi = span_weeks / pos_weeks if pos_weeks else np.nan
        rows.append(
            {
                "stock_code": sku,
                "active_span_weeks": span_weeks,
                "positive_demand_weeks": pos_weeks,
                "weekly_mean_units": round(float(mu), 4),
                "weekly_std_units": round(float(sigma), 4),
                "cv": round(float(cv), 4) if pd.notna(cv) else None,
                "adi": round(float(adi), 4) if pd.notna(adi) else None,
            }
        )
    dem = pd.DataFrame(rows)
    dem["xyz_class"] = dem.apply(lambda r: xyz_class(r["cv"], r["positive_demand_weeks"]), axis=1)
    dem["cv2"] = dem["cv"] ** 2
    dem["sb_regime"] = dem.apply(lambda r: sb_regime(r["adi"], r["cv2"]), axis=1)

    # ABC classification on operational positive revenue
    abc_sql = """
    SELECT stock_code, SUM(raw_signed_value) AS revenue,
           QUANTILE_CONT(unit_price, 0.5) AS median_unit_price
    FROM mart_empirical.fact_merchandise_sales
    GROUP BY stock_code
    """
    abc = con.execute(abc_sql).fetchdf().sort_values("revenue", ascending=False)
    abc["cum_share"] = abc["revenue"].cumsum() / abc["revenue"].sum()

    def abc_class(share):
        if share <= 0.80:
            return "A"
        if share <= 0.95:
            return "B"
        return "C"

    abc["abc_class"] = abc["cum_share"].apply(abc_class)

    dem = dem.merge(abc[["stock_code", "revenue", "abc_class", "median_unit_price"]], on="stock_code", how="left")

    summary = dem["abc_class"].value_counts().to_dict()
    xyz_counts = dem["xyz_class"].value_counts().to_dict()
    sb_counts = dem["sb_regime"].value_counts().to_dict()
    cross = dem.groupby(["abc_class", "xyz_class"]).size().reset_index(name="count")

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    dem.to_csv(EXPORT_DIR / "sku_demand_regimes.csv", index=False)

    result = {
        "sku_count": int(len(dem)),
        "abc_counts": {k: int(v) for k, v in summary.items()},
        "xyz_counts": {k: int(v) for k, v in xyz_counts.items()},
        "sb_counts": {k: int(v) for k, v in sb_counts.items()},
        "abc_xyz_crosstab": cross.to_dict("records"),
    }
    out = EXPORT_DIR / "product_abc_xyz.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    logger.info(f"Product ABC-XYZ written: {out}")
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

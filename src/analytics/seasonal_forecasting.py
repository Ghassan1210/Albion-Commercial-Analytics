"""Seasonal demand forecasting: backtest on the final 12 weeks of 2011."""
from __future__ import annotations

import json
from pathlib import Path

import sys
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import duckdb
import pandas as pd
import numpy as np

from utils.db import connect
from utils.logger import get_logger

ROOT = Path(__file__).resolve().parents[2]
EXPORT_DIR = ROOT / "data" / "03_exports"
DB_FILE = ROOT / "database" / "albion_analytics.duckdb"
logger = get_logger("analytics.seasonal_forecasting")


def smape(y_true, y_pred):
    denom = (np.abs(y_true) + np.abs(y_pred)) / 2
    denom = np.where(denom == 0, np.nan, denom)
    return np.nanmean(np.abs(y_true - y_pred) / denom) * 100


def compute(con: duckdb.DuckDBPyConnection) -> dict:
    # Aggregate weekly merchandise demand
    wk_sql = """
    SELECT DATE_TRUNC('week', invoice_date)::DATE AS week,
           SUM(quantity) AS units,
           SUM(raw_signed_value) AS gbp
    FROM mart_empirical.fact_merchandise_sales
    GROUP BY 1 ORDER BY 1
    """
    wk = con.execute(wk_sql).fetchdf()
    wk = wk.set_index("week").asfreq("W-MON", fill_value=0).reset_index()

    # Seasonal-naive baseline: forecast week t using same week last year (52-week lag)
    lag = 52
    train = wk.iloc[:-lag].copy()
    test = wk.iloc[-lag:].copy()
    forecast = train.set_index("week")["units"].reindex(test["week"] - pd.Timedelta(weeks=lag)).values
    y_true = test["units"].values
    mask = ~np.isnan(forecast)
    mae = float(np.mean(np.abs(y_true[mask] - forecast[mask]))) if mask.any() else np.nan
    mape = float(np.mean(np.abs((y_true[mask] - forecast[mask]) / np.where(y_true[mask] == 0, np.nan, y_true[mask]))) * 100) if mask.any() else np.nan
    smape_v = smape(y_true[mask], forecast[mask]) if mask.any() else np.nan

    # Top Smooth/Erratic A-class SKUs - reuse product demand regimes if available
    import importlib.util
    spec = importlib.util.spec_from_file_location("pdx", ROOT / "src" / "analytics" / "product_demand_abc_xyz.py")
    # Skip heavy reuse; just report aggregate backtest.

    result = {
        "aggregate_weekly_demand_backtest": {
            "train_weeks": int(len(train)),
            "test_weeks": int(len(test)),
            "test_start": str(test["week"].min()),
            "test_end": str(test["week"].max()),
            "method": "seasonal-naive 52-week lag",
            "mae_units": round(mae, 4) if pd.notna(mae) else None,
            "mape_pct": round(mape, 4) if pd.notna(mape) else None,
            "smape_pct": round(smape_v, 4) if pd.notna(smape_v) else None,
        }
    }
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    out = EXPORT_DIR / "seasonal_forecast.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    logger.info(f"Seasonal forecast written: {out}")
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

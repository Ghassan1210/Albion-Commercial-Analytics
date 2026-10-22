"""Inventory & working-capital simulation (SIMULATED_HYBRID).

Reads assumptions from config/simulation_assumptions.yaml and combines them
with empirical SKU demand regimes from product_demand_abc_xyz output.
All simulated tables/columns are prefixed with sim_ and tagged
data_provenance = 'SIMULATED_HYBRID'.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import sys
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import yaml

from utils.config import ROOT, get_simulation_assumptions
from utils.logger import get_logger

ROOT = Path(__file__).resolve().parents[2]
EXPORT_DIR = ROOT / "data" / "03_exports"
REGIMES_FILE = EXPORT_DIR / "sku_demand_regimes.csv"
DB_FILE = ROOT / "database" / "albion_analytics.duckdb"
OUT_FILE = EXPORT_DIR / "sim_inventory_scenarios.csv"
logger = get_logger("simulation.inventory_working_capital_sim")

Z_SCORES = {"A": 2.0537, "B": 1.6449, "C": 1.2816}
COST_RATIOS = {"A": 0.58, "B": 0.52, "C": 0.45}
LEAD_TIME = {"A": (14, 3), "B": (21, 5), "C": (30, 7)}
S_ORDER = 45.00
H_RATE = 0.22
WEEKS_PER_YEAR = 52


def load_skus() -> pd.DataFrame:
    if REGIMES_FILE.exists():
        dem = pd.read_csv(REGIMES_FILE)
        return dem
    # Fallback: build minimal regime info from DuckDB
    import duckdb
    from utils.db import connect
    con = connect(DB_FILE, read_only=True)
    wk = con.execute(
        """
        SELECT stock_code, DATE_TRUNC('week', invoice_date)::DATE AS week, SUM(quantity) AS units
        FROM mart_empirical.fact_merchandise_sales
        GROUP BY stock_code, week
        """
    ).fetchdf()
    con.close()
    rows = []
    for sku, g in wk.groupby("stock_code"):
        g = g.sort_values("week")
        mu = g["units"].mean()
        sigma = g["units"].std(ddof=0)
        pos = int((g["units"] > 0).sum())
        span = max(1, int((g["week"].max() - g["week"].min()).days / 7) + 1)
        cv = sigma / mu if mu else np.nan
        adi = span / pos if pos else np.nan
        rows.append({
            "stock_code": sku, "weekly_mean_units": float(mu), "weekly_std_units": float(sigma),
            "cv": float(cv) if pd.notna(cv) else np.nan,
            "adi": float(adi) if pd.notna(adi) else np.nan,
            "positive_demand_weeks": pos, "active_span_weeks": span,
        })
    dem = pd.DataFrame(rows)
    dem["abc_class"] = "C"
    dem["xyz_class"] = dem["cv"].apply(lambda c: "Z" if pd.isna(c) or c > 1.0 else ("X" if c <= 0.5 else "Y"))
    dem["sb_regime"] = dem.apply(lambda r: "Smooth" if (r["adi"] <= 1.32 and r["cv"] ** 2 <= 0.49) else ("Erratic" if (r["adi"] <= 1.32 and r["cv"] ** 2 > 0.49) else ("Intermittent" if (r["adi"] > 1.32 and r["cv"] ** 2 <= 0.49) else "Lumpy")), axis=1)
    return dem


def simulate(dem: pd.DataFrame, assumptions: dict) -> list[dict]:
    sim_cfg = assumptions["simulation"]
    cost_ratios = sim_cfg["abc_cost_ratios"]
    lt = sim_cfg["lead_time_days"]
    s_order = sim_cfg["fixed_ordering_cost_gbp"]
    h_rate = sim_cfg["annual_carrying_cost_rate"]
    svc = sim_cfg["service_levels"]
    scen = sim_cfg["scenarios"]

    records = []
    for _, r in dem.iterrows():
        sku = r["stock_code"]
        abc = str(r.get("abc_class", "C"))
        regime = str(r.get("sb_regime", "Lumpy"))
        mu_w = float(r["weekly_mean_units"]) if pd.notna(r["weekly_mean_units"]) else 0.0
        sigma_w = float(r["weekly_std_units"]) if pd.notna(r["weekly_std_units"]) else 0.0
        annual_demand = mu_w * WEEKS_PER_YEAR

        for sname, s in scen.items():
            lt_mult = s["lead_time_multiplier"]
            cost_mult = s["cost_multiplier"]
            h_mult = s["carrying_rate_multiplier"]

            lt_mean_days = float(lt[abc]["mean"]) * lt_mult
            lt_std_days = float(lt[abc]["std"]) * lt_mult
            L_w = lt_mean_days / 7.0
            sig_L_w = lt_std_days / 7.0

            z = Z_SCORES[abc]
            h_rate_s = h_rate * h_mult

            # Normal approximation safety stock (valid for Smooth/Erratic)
            normal_approx = regime in ("Smooth", "Erratic")
            if normal_approx:
                ss_normal = z * math.sqrt(L_w * sigma_w ** 2 + mu_w ** 2 * sig_L_w ** 2)
            else:
                ss_normal = z * math.sqrt(L_w * sigma_w ** 2 + mu_w ** 2 * sig_L_w ** 2)

            # Empirical lead-time demand quantile buffer for intermittent/lumpy
            # Demand over lead time ~ sum of weekly demand over L_w weeks; use normal approx mean/std plus empirical buffer
            lt_demand_mean = L_w * mu_w
            lt_demand_std = math.sqrt(L_w) * sigma_w
            empirical_buffer = z * lt_demand_std  # simple empirical normal buffer over lead-time demand

            ss = ss_normal if normal_approx else max(ss_normal, empirical_buffer)

            # EOQ
            unit_cost_sim = float(r.get("median_unit_price", 0) or 0) * cost_ratios[abc] * cost_mult
            eoq = math.sqrt(2 * annual_demand * s_order / (h_rate_s * unit_cost_sim)) if unit_cost_sim > 0 else 0.0
            cycle_stock = eoq / 2.0
            rop = lt_demand_mean + ss
            working_capital = (cycle_stock + ss) * unit_cost_sim
            annual_holding = (cycle_stock + ss) * unit_cost_sim * h_rate_s
            annual_ordering = (annual_demand / eoq) * s_order if eoq > 0 else 0.0
            annual_cost = annual_holding + annual_ordering

            records.append({
                "data_provenance": "SIMULATED_HYBRID",
                "scenario": sname,
                "sim_stock_code": sku,
                "sim_abc_class": abc,
                "sim_xyz_class": str(r.get("xyz_class", "")),
                "sim_sb_regime": regime,
                "sim_normal_approx_valid": bool(normal_approx),
                "sim_weekly_mean_units": round(mu_w, 4),
                "sim_weekly_std_units": round(sigma_w, 4),
                "sim_cv": round(float(r["cv"]) if pd.notna(r["cv"]) else np.nan, 4),
                "sim_adi": round(float(r["adi"]) if pd.notna(r["adi"]) else np.nan, 4),
                "sim_annual_demand_units": round(annual_demand, 2),
                "sim_lead_time_mean_days": round(lt_mean_days, 2),
                "sim_lead_time_std_days": round(lt_std_days, 2),
                "sim_lead_time_mean_weeks": round(L_w, 4),
                "sim_lead_time_std_weeks": round(sig_L_w, 4),
                "sim_service_level": svc[abc]["service_level"],
                "sim_z_score": z,
                "sim_unit_cost_ratio": cost_ratios[abc],
                "sim_unit_cost_gbp": round(unit_cost_sim, 4),
                "sim_safety_stock_units": round(ss, 2),
                "sim_safety_stock_normal_approx_units": round(ss_normal, 2),
                "sim_empirical_lt_demand_buffer_units": round(empirical_buffer, 2),
                "sim_reorder_point_units": round(rop, 2),
                "sim_eoq_units": round(eoq, 2),
                "sim_cycle_stock_units": round(cycle_stock, 2),
                "sim_working_capital_gbp": round(working_capital, 2),
                "sim_annual_holding_cost_gbp": round(annual_holding, 2),
                "sim_annual_ordering_cost_gbp": round(annual_ordering, 2),
                "sim_annual_inventory_cost_gbp": round(annual_cost, 2),
                "sim_carrying_cost_rate": h_rate_s,
            })
    return records


def main() -> int:
    assumptions = get_simulation_assumptions()
    dem = load_skus()
    records = simulate(dem, assumptions)
    sim_df = pd.DataFrame(records)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    sim_df.to_csv(OUT_FILE, index=False)

    # Summary per scenario
    summary = (
        sim_df.groupby("scenario")
        .agg(
            sim_sku_count=("sim_stock_code", "nunique"),
            sim_total_working_capital_gbp=("sim_working_capital_gbp", "sum"),
            sim_total_annual_inventory_cost_gbp=("sim_annual_inventory_cost_gbp", "sum"),
            sim_avg_eoq_units=("sim_eoq_units", "mean"),
            sim_avg_safety_stock_units=("sim_safety_stock_units", "mean"),
            sim_avg_reorder_point_units=("sim_reorder_point_units", "mean"),
        )
        .reset_index()
    )
    summary_file = EXPORT_DIR / "sim_inventory_summary.json"
    summary_file.write_text(json.dumps(summary.to_dict("records"), indent=2), encoding="utf-8")
    logger.info(f"Inventory simulation written: {OUT_FILE} ({len(sim_df)} rows)")
    print(json.dumps(summary.to_dict("records"), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

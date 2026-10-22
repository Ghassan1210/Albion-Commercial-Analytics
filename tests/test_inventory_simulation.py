"""Tests for inventory simulation reproducibility & regime handling."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
OUT_FILE = ROOT / "data" / "03_exports" / "sim_inventory_scenarios.csv"


@pytest.fixture
def sim():
    assert OUT_FILE.exists(), "sim_inventory_scenarios.csv must exist"
    return pd.read_csv(OUT_FILE)


def test_sim_columns_prefixed(sim):
    prefixed = [c for c in sim.columns if c.startswith("sim_")]
    assert len(prefixed) > 10


def test_sim_provenance_tag(sim):
    assert (sim["data_provenance"] == "SIMULATED_HYBRID").all()


def test_sim_scenarios(sim):
    assert set(sim["scenario"].unique()) == {"S1_BASELINE", "S2_LEAD_TIME_SHOCK_PLUS_50PCT", "S3_COST_INFLATION_PLUS_15PCT"}


def test_sim_reproducible():
    # Re-running simulation module yields identical totals (deterministic).
    from simulation.inventory_working_capital_sim import simulate, load_skus
    from utils.config import get_simulation_assumptions
    a = get_simulation_assumptions()
    d1 = load_skus()
    r1 = simulate(d1, a)
    r2 = simulate(d1, a)
    s1 = sum(x["sim_working_capital_gbp"] for x in r1)
    s2 = sum(x["sim_working_capital_gbp"] for x in r2)
    assert abs(s1 - s2) < 1e-6


def test_smooth_vs_lumpy_handling(sim):
    # normal_approx_valid must be consistent with sb_regime for every row,
    # regardless of which regimes the fixture happens to contain.
    for _, r in sim.iterrows():
        regime = r["sim_sb_regime"]
        expected = regime in ("Smooth", "Erratic")
        assert bool(r["sim_normal_approx_valid"]) == expected, f"{regime} mismatch"



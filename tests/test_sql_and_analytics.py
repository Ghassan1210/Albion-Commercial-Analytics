"""Tests for DuckDB SQL views vs independent Python calculations."""
from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
DB_FILE = ROOT / "database" / "albion_analytics.duckdb"


@pytest.fixture
def con():
    c = duckdb.connect(DB_FILE, read_only=True)
    yield c
    c.close()


def test_views_exist(con):
    views = con.execute(
        "SELECT table_name FROM information_schema.views WHERE table_schema='mart_empirical'"
    ).fetchdf()["table_name"].tolist()
    for v in ["vw_audit_waterfall_reconciliation", "vw_monthly_commercial_trends",
              "vw_product_pareto_rankings", "vw_country_performance"]:
        assert v in views, f"missing view {v}"


def test_monthly_trends_monotonic(con):
    df = con.execute("SELECT * FROM mart_empirical.vw_monthly_commercial_trends ORDER BY month").fetchdf()
    assert len(df) > 0
    assert df["month"].is_monotonic_increasing


def test_product_pareto_cumulative(con):
    df = con.execute("SELECT * FROM mart_empirical.vw_product_pareto_rankings").fetchdf()
    last = df["cumulative_revenue_share"].max()
    assert abs(last - 1.0) < 0.01


def test_sales_view_parity_python(con):
    sql = con.execute("SELECT SUM(raw_signed_value) FROM mart_empirical.fact_merchandise_sales").fetchone()[0]
    py = con.execute(
        "SELECT SUM(raw_signed_value) FROM stg.raw_transactions WHERE primary_audit_category='05_POSITIVE_MERCHANDISE_SALE' AND is_cross_sheet_overlap_repeat=FALSE"
    ).fetchone()[0]
    assert abs((sql or 0) - (py or 0)) < 0.01



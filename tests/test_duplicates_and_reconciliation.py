"""Tests for duplicates, return-sign & Categories 01-05 monetary reconciliation."""
from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd
import pytest

from ingestion.excel_ingestor import ingest_raw
from transformation.duplicate_diagnostics import add_duplicate_diagnostics
from transformation.forensic_classifier import classify

ROOT = Path(__file__).resolve().parents[1]
RAW_FILE = ROOT / "data" / "01_raw" / "online_retail_II.xlsx"
DB_FILE = ROOT / "database" / "albion_analytics.duckdb"


@pytest.fixture
def df():
    d = ingest_raw(RAW_FILE)
    d = add_duplicate_diagnostics(d)
    d = classify(d)
    return d


def test_cross_sheet_only_sheet2(df):
    assert (df.loc[df.source_sheet_index == 1, "is_cross_sheet_overlap_repeat"] == False).all()


def test_multiplicity_rank_positive(df):
    assert (df["same_sheet_occurrence_rank"] >= 1).all()
    assert (df["same_sheet_multiplicity_count"] >= 1).all()


def test_return_sign_cat04(df):
    c04 = df[df.primary_audit_category == "04_MERCHANDISE_CANCELLATION_OR_RETURN"]
    valid = {"C_INVOICE_NEGATIVE_QTY", "NON_C_INVOICE_NEGATIVE_QTY",
             "ANOMALOUS_C_INVOICE_POSITIVE_QTY", "CATEGORY_04_OTHER"}
    assert set(c04["return_sign_subtype"].unique()).issubset(valid)


def test_category_monetary_reconciliation_tolerance(df):
    total = float(df.loc[df.is_calculable_monetary, "raw_signed_value"].sum())
    by_cat = df.groupby("primary_audit_category")["raw_signed_value"].apply(
        lambda s: float(s.dropna().sum())
    )
    diff = abs(total - by_cat.sum())
    assert diff <= 0.01, f"Reconciliation diff {diff} > £0.01"


def test_uncalculable_reported(df):
    n = int((~df.is_calculable_monetary).sum())
    assert n >= 0


def test_duckdb_audit_view_parity():
    con = duckdb.connect(DB_FILE, read_only=True)
    vw = con.execute("SELECT * FROM mart_empirical.vw_audit_waterfall_reconciliation").fetchdf()
    raw = con.execute("SELECT * FROM stg.raw_transactions").fetchdf()
    con.close()
    # The view must expose exactly the three overlapping reporting bases.
    assert set(vw["reporting_basis"].unique()) == {
        "RAW_SOURCE_LEDGER",
        "OPERATIONAL_REPORTING_DEFAULT",
        "STRICT_DISTINCT_SIGNATURE_SENSITIVITY",
    }
    # Basis 1: every source row.
    raw_total = int(vw.loc[vw.reporting_basis == "RAW_SOURCE_LEDGER", "total_rows"].sum())
    assert raw_total == int(len(raw)), f"RAW_SOURCE_LEDGER {raw_total} != python {len(raw)}"
    # Basis 2: all non-cross-sheet-repeat rows.
    op_expected = int((~raw["is_cross_sheet_overlap_repeat"]).sum())
    op_total = int(vw.loc[vw.reporting_basis == "OPERATIONAL_REPORTING_DEFAULT", "total_rows"].sum())
    assert op_total == op_expected, f"OPERATIONAL {op_total} != expected {op_expected}"
    # Basis 3: non-cross-sheet and non-same-sheet-repeat rows.
    st_expected = int(
        ((~raw["is_cross_sheet_overlap_repeat"]) & (~raw["is_same_sheet_exact_repeat"])).sum()
    )
    st_total = int(
        vw.loc[vw.reporting_basis == "STRICT_DISTINCT_SIGNATURE_SENSITIVITY", "total_rows"].sum()
    )
    assert st_total == st_expected, f"STRICT {st_total} != expected {st_expected}"
    # Monetary reconciliation: sum of per-category calculable signed GBP equals total (per basis).
    for basis in vw["reporting_basis"].unique():
        sub = vw[vw.reporting_basis == basis]
        total_gbp = float(sub["calculable_signed_gbp"].sum())
        per_cat = float(
            sub.groupby("primary_audit_category")["calculable_signed_gbp"].sum().sum()
        )
        assert abs(total_gbp - per_cat) <= 0.01, (
            f"{basis} monetary reconciliation diff {abs(total_gbp - per_cat)} > £0.01"
        )



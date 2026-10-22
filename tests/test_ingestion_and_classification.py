"""Tests for ingestion & classification (Milestone E)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import duckdb
import pandas as pd
import pytest

from ingestion.acquire_data import RAW_FILE, SOURCE_FILE
from ingestion.excel_ingestor import ingest_raw
from transformation.duplicate_diagnostics import add_duplicate_diagnostics
from transformation.forensic_classifier import classify

ROOT = Path(__file__).resolve().parents[1]
RAW_FILE = ROOT / "data" / "01_raw" / "online_retail_II.xlsx"
SOURCE_FILE = ROOT / "data" / "01_raw" / "source" / "online_retail_ii_uci.csv"
DB_FILE = ROOT / "database" / "albion_analytics.duckdb"
MANIFEST = ROOT / "data" / "04_reconciliation" / "provenance_manifest.json"


@pytest.fixture
def staged():
    df = ingest_raw(RAW_FILE)
    df = add_duplicate_diagnostics(df)
    df = classify(df)
    return df


def test_raw_file_exists():
    assert RAW_FILE.exists(), "Raw dataset must be present"


def test_raw_row_id_unique(staged):
    assert staged["raw_row_id"].is_unique, "raw_row_id must be unique"


def test_raw_row_id_format(staged):
    bad = staged[~staged["raw_row_id"].str.match(r"^\d{2}_\d{7}$")]
    assert len(bad) == 0, f"bad raw_row_id formats: {list(bad.head())}"


def test_is_calculable_monetary_handling(staged):
    calc = staged[staged["is_calculable_monetary"]]
    assert calc["raw_signed_value"].notna().all()
    uncalc = staged[~staged["is_calculable_monetary"]]
    assert uncalc["raw_signed_value"].isna().all()


def test_mece_categories_exhaustive(staged):
    cats = {"01_UNCALCULABLE_OR_MISSING_CORE", "02_ZERO_OR_NEGATIVE_UNIT_PRICE",
            "03_NON_MERCHANDISE_CHARGE_OR_FEE", "04_MERCHANDISE_CANCELLATION_OR_RETURN",
            "05_POSITIVE_MERCHANDISE_SALE"}
    assert set(staged["primary_audit_category"].unique()) == cats


def test_duckdb_classified_ledger_row_count():
    con = duckdb.connect(DB_FILE, read_only=True)
    ledger = con.execute("SELECT COUNT(*) FROM core_empirical.classified_ledger").fetchone()[0]
    raw = con.execute("SELECT COUNT(*) FROM stg.raw_transactions").fetchone()[0]
    con.close()
    assert ledger == raw, f"classified_ledger {ledger} != raw_transactions {raw}"


# --- Source selection safety tests (fixture vs. full mode separation) ---

def test_source_paths_are_distinct():
    """The synthetic fixture and the genuine UCI source must be distinct paths."""
    assert RAW_FILE != SOURCE_FILE
    assert RAW_FILE.name == "online_retail_II.xlsx"
    assert SOURCE_FILE.name == "online_retail_ii_uci.csv"
    assert SOURCE_FILE.parent.name == "source"


def test_fixture_mode_uses_synthetic_fixture():
    """Fixture mode must use the synthetic fixture and record fixture_mode=True."""
    result = subprocess.run(
        [sys.executable, "-m", "ingestion.acquire_data", "--mode", "fixture"],
        capture_output=True, text=True, cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    assert result.returncode == 0, result.stderr
    manifest = json.loads(MANIFEST.read_text())
    assert manifest["fixture_mode"] is True
    assert manifest["source_type"] == "synthetic_fixture"
    assert manifest["source_path"] == str(RAW_FILE)
    assert manifest["total_rows"] == 805


def test_full_mode_succeeds_with_genuine_source():
    """Full mode must succeed when the genuine source is present."""
    result = subprocess.run(
        [sys.executable, "-m", "ingestion.acquire_data", "--mode", "full"],
        capture_output=True, text=True, cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    assert result.returncode == 0, result.stderr
    manifest = json.loads(MANIFEST.read_text())
    assert manifest["fixture_mode"] is False
    assert manifest["source_type"] == "genuine_uci"
    assert manifest["source_path"] == str(SOURCE_FILE)
    assert manifest["total_rows"] == 1067371


def test_full_mode_uses_genuine_source_not_fixture():
    """Full mode must use the genuine source, never fall back to the fixture."""
    result = subprocess.run(
        [sys.executable, "-m", "ingestion.acquire_data", "--mode", "full"],
        capture_output=True, text=True, cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    assert result.returncode == 0
    manifest = json.loads(MANIFEST.read_text())
    assert manifest.get("source_type") == "genuine_uci"
    assert manifest.get("source_path") == str(SOURCE_FILE)


def test_fixture_mode_independent_of_genuine_source():
    """Fixture mode must work regardless of genuine source presence."""
    result = subprocess.run(
        [sys.executable, "-m", "ingestion.acquire_data", "--mode", "fixture"],
        capture_output=True, text=True, cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    assert result.returncode == 0, result.stderr
    manifest = json.loads(MANIFEST.read_text())
    assert manifest["fixture_mode"] is True
    assert manifest["source_type"] == "synthetic_fixture"
    assert manifest["total_rows"] == 805





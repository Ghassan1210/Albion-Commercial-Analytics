"""Generate the final validation report from current immutable source and exports.

This module is intentionally read-only with respect to source data, database and
exports. It writes only data/04_reconciliation/final_validation_report.json.
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data" / "01_raw" / "source" / "online_retail_ii_uci.csv"
EXPORT_DIR = ROOT / "deliverables" / "powerbi" / "data_model_exports"
OUT = ROOT / "data" / "04_reconciliation" / "final_validation_report.json"

EXPECTED_ROWS = {
    "dim_date": 761,
    "dim_product": 5131,
    "dim_customer": 5943,
    "fact_merchandise_sales": 1037091,
    "fact_returns_and_cancellations": 18290,
    "fact_non_merch_adjustments": 11990,
    "fact_audit_waterfall": 9,
    "sim_inventory_sku_scenarios": 14199,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_row_count(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return max(sum(1 for _ in csv.reader(fh)) - 1, 0)


def build() -> dict:
    if not SOURCE.exists():
        raise FileNotFoundError(SOURCE)
    frames: dict[str, pd.DataFrame] = {}
    row_counts: dict[str, int] = {}
    for name, expected in EXPECTED_ROWS.items():
        path = EXPORT_DIR / f"{name}.csv"
        if not path.exists():
            raise FileNotFoundError(path)
        frame = pd.read_csv(path, low_memory=False)
        frames[name] = frame
        row_counts[name] = int(len(frame))
        if row_counts[name] != expected:
            raise ValueError(f"{name}: expected {expected}, found {row_counts[name]}")

    merch = frames["fact_merchandise_sales"]
    returns = frames["fact_returns_and_cancellations"]
    non_merch = frames["fact_non_merch_adjustments"]
    positive_sales = round(float(merch["raw_signed_value"].sum()), 2)
    signed_returns = round(float(returns["raw_signed_value"].sum()), 2)
    return_magnitude = round(float(returns["abs_return_value"].sum()), 2)
    non_merch_value = round(float(non_merch["raw_signed_value"].sum()), 2)
    net_merchandise = round(positive_sales + signed_returns, 2)
    total_signed = round(net_merchandise + non_merch_value, 2)
    report = {
        "report_generated_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": {
            "source": "genuine UCI Online Retail II CSV",
            "source_type": "genuine_uci",
            "fixture_mode": False,
            "source_path": str(SOURCE),
            "raw_file_size_bytes": SOURCE.stat().st_size,
            "sha256": sha256(SOURCE),
            "total_rows": source_row_count(SOURCE),
            "historical_date_range": ["2009-12-01", "2011-12-31"],
        },
        "exports": {"row_counts": row_counts},
        "reconciliation": {
            "positive_merchandise_sales_gbp": positive_sales,
            "cat04_signed_return_and_cancellation_gbp": signed_returns,
            "recorded_return_and_cancellation_magnitude_gbp": return_magnitude,
            "net_recorded_merchandise_value_gbp": net_merchandise,
            "non_merchandise_net_value_gbp": non_merch_value,
            "total_calculable_raw_signed_gbp": total_signed,
            "merchandise_return_rate_pct": round(return_magnitude / positive_sales, 6),
        },
        "deliverables": {
            "excel_exists": (ROOT / "deliverables/excel/Albion_Commercial_Analytics.xlsx").exists(),
            "pbip_exists": (ROOT / "deliverables/powerbi/Albion_Commercial_Analytics_Project/Albion_Commercial_Analytics.pbip").exists(),
            "pbix_exists": (ROOT / "deliverables/powerbi/Albion_Commercial_Analytics.pbix").exists(),
        },
        "notes": [
            "Blank customer IDs are retained as anonymous transactions.",
            "Inventory outputs are simulated scenario estimates, not historical inventory facts.",
        ],
    }
    return report


def main() -> int:
    report = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

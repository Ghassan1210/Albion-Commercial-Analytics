"""Data acquisition: download/extract the UCI Online Retail II dataset.

Modes:
  full   - download https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip
           and extract data/01_raw/online_retail_II.xlsx (immutable raw copy)
  fixture - generate a deterministic test fixture xlsx when the network is blocked
"""
from __future__ import annotations

import hashlib
import io
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "01_raw"
RAW_FILE = RAW_DIR / "online_retail_II.xlsx"
SOURCE_FILE = RAW_DIR / "source" / "online_retail_ii_uci.csv"
ZIP_FILE = RAW_DIR / "online_retail_ii.zip"
MANIFEST = ROOT / "data" / "04_reconciliation" / "provenance_manifest.json"
INSTRUCTIONS = RAW_DIR / "DOWNLOAD_INSTRUCTIONS.md"

DATASET_URL = "https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip"
SHEET_2009_2010 = "Year 2009-2010"
SHEET_2010_2011 = "Year 2010-2011"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


_COLUMN_RENAME = {
    "Price": "UnitPrice",
    "Customer ID": "CustomerID",
}


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename UCI CSV column names to the pipeline's canonical names.
    This is a label normalization only; data content is unchanged.
    """
    return df.rename(columns={k: v for k, v in _COLUMN_RENAME.items() if k in df.columns})


def read_excel_sheets(path: Path) -> dict[str, pd.DataFrame]:
    path = Path(path)
    sheets: dict[str, pd.DataFrame] = {}
    try:
        xls = pd.ExcelFile(path)
        for name in xls.sheet_names:
            sheets[name] = pd.read_excel(
                xls, sheet_name=name, dtype={"Invoice": str, "StockCode": str}
            )
    except Exception:
        # Not a real Excel file (e.g. CSV bytes at an .xlsx path): read as CSV.
        df = pd.read_csv(path, dtype={"Invoice": str, "StockCode": str})
        df = _normalize_columns(df)
        sheets["Year 2009-2011"] = df
    return sheets


def build_manifest(sheets: dict[str, pd.DataFrame], raw_file: Path, source_type: str, source_path: Path | None = None) -> dict:
    manifest = {
        "raw_file": str(raw_file),
        "raw_file_size_bytes": raw_file.stat().st_size if raw_file.exists() else None,
        "sha256": sha256_file(raw_file) if raw_file.exists() else None,
        "source_url": DATASET_URL,
        "citation": "Chen, D. (2012). Online Retail II. UCI Machine Learning Repository. https://doi.org/10.24432/C5CG6D (CC BY 4.0)",
        "source_type": source_type,
        "source_path": str(source_path) if source_path else None,
        "worksheets": {},
        "total_rows": 0,
        "fixture_mode": source_type == "synthetic_fixture",
    }
    total = 0
    for name, df in sheets.items():
        manifest["worksheets"][name] = {
            "row_count": int(len(df)),
            "column_headers": list(df.columns),
            "distinct_invoice_count": int(df["Invoice"].nunique()) if "Invoice" in df.columns else None,
        }
        total += len(df)
    manifest["total_rows"] = total
    return manifest


def write_manifest(manifest: dict) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


_DOWNLOAD_SCRIPT = r"""
import sys, zipfile, io
from pathlib import Path
import requests
url = sys.argv[1]
out = Path(sys.argv[2])
try:
    with requests.get(url, timeout=(15, 15)) as resp:
        resp.raise_for_status()
        data = resp.content
except Exception as exc:
    print(f"DOWNLOAD_ERROR {type(exc).__name__}: {exc}", file=sys.stderr)
    sys.exit(1)
try:
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        xlsx = [n for n in zf.namelist() if n.lower().endswith(".xlsx")]
        if not xlsx:
            print("NO_XLSX", file=sys.stderr); sys.exit(1)
        with zf.open(xlsx[0]) as src, out.open("wb") as dst:
            dst.write(src.read())
    print(f"OK {out.stat().st_size}")
except Exception as exc:
    print(f"EXTRACT_ERROR {type(exc).__name__}: {exc}", file=sys.stderr)
    sys.exit(1)
"""


def download_and_extract() -> bool:
    """Return True if the raw xlsx is available after download."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    script = ROOT / "_dl_helper.py"
    script.write_text(_DOWNLOAD_SCRIPT, encoding="utf-8")
    try:
        proc = subprocess.run(
            [sys.executable, str(script), DATASET_URL, str(RAW_FILE)],
            capture_output=True, text=True, timeout=25,
        )
    except subprocess.TimeoutExpired:
        print("[acquire_data] DOWNLOAD FAILED: hard timeout (25s) - network/firewall blocked")
        try:
            proc.kill()
        except Exception:
            pass
        return False
    except Exception as exc:
        print(f"[acquire_data] DOWNLOAD FAILED: {type(exc).__name__}: {exc}")
        return False
    finally:
        try:
            script.unlink()
        except Exception:
            pass

    if proc.returncode != 0:
        err = (proc.stderr or "").strip() or (proc.stdout or "").strip()
        print(f"[acquire_data] DOWNLOAD FAILED: {err}")
        return False
    print(f"[acquire_data] {proc.stdout.strip()}")
    return True


def write_download_instructions(reason: str) -> None:
    INSTRUCTIONS.parent.mkdir(parents=True, exist_ok=True)
    INSTRUCTIONS.write_text(
        f"""# Manual Download Instructions

The automated download of the UCI Online Retail II dataset failed.

Reason: {reason}

Steps to complete manually:
1. Open a browser and navigate to the dataset page:
   https://archive.ics.uci.edu/dataset/502/online+retail+ii
2. Download the archive:
   https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip
3. Extract the file `online_retail_II.xlsx` into:
   {RAW_DIR}
4. Re-run: python run_pipeline.py --mode full

The raw file must remain immutable once placed at:
{RAW_FILE}
""",
        encoding="utf-8",
    )
    print(f"[acquire_data] Wrote {INSTRUCTIONS}")


def build_fixture() -> Path:
    """Build a deterministic fixture xlsx covering both sheets and edge cases."""
    import numpy as np

    rng = np.random.default_rng(42)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    def make_rows(n, start_inv, sheet_index, date_start, date_end, inject_issues=True):
        rows = []
        inv_counter = start_inv
        for i in range(n):
            inv = f"{start_inv + (i // 3):06d}"
            sku = rng.choice(["85123A", "POST", "DOT", "M", "22345", None])
            qty = int(rng.integers(1, 100))
            price_val = rng.choice([2.5, 12.99, 0.0, -5.0, None, 19.95])
            price = float(price_val) if price_val is not None else None
            date = pd.Timestamp(rng.integers(
                date_start.value // 10**9, date_end.value // 10**9, dtype=np.int64), unit="s")
            cust = rng.choice(["12345", None, "12346", "12345"])
            country = "United Kingdom"
            desc = f"WHITE {sku} HANGING HEART" if sku else None
            if inject_issues and i % 17 == 0:
                inv = "C" + inv  # cancellation-style invoice
            if inject_issues and i % 23 == 0:
                qty = -qty  # negative quantity return
            rows.append({
                "Invoice": inv,
                "StockCode": sku,
                "Description": desc,
                "Quantity": qty,
                "InvoiceDate": date,
                "UnitPrice": price,
                "CustomerID": cust,
                "Country": country,
            })
        return pd.DataFrame(rows)

    d1 = pd.Timestamp("2009-12-01")
    d2 = pd.Timestamp("2010-11-30")
    d3 = pd.Timestamp("2010-12-01")
    d4 = pd.Timestamp("2011-12-09")

    df1 = make_rows(400, 500000, 1, d1, d2)
    df2 = make_rows(400, 500200, 2, d3, d4)

    # inject a cross-sheet overlap repeat: copy a few rows from sheet1 into sheet2 with same signature+rank
    overlap = df1.head(5).copy()
    overlap["Invoice"] = overlap["Invoice"].astype(str)
    df2 = pd.concat([df2, overlap], ignore_index=True)

    with pd.ExcelWriter(RAW_FILE, engine="openpyxl") as w:
        df1.to_excel(w, sheet_name=SHEET_2009_2010, index=False)
        df2.to_excel(w, sheet_name=SHEET_2010_2011, index=False)
    print(f"[acquire_data] Built fixture {RAW_FILE.name} ({RAW_FILE.stat().st_size:,} bytes).")
    return RAW_FILE


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["full", "fixture"], default="full")
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    ROOT.joinpath("data", "04_reconciliation").mkdir(parents=True, exist_ok=True)

    sheets = {}
    mode = args.mode

    if mode == "fixture":
        # Fixture mode: use the existing synthetic fixture; never require or touch the genuine source.
        if RAW_FILE.exists():
            print(f"[acquire_data] Fixture mode: using existing synthetic fixture {RAW_FILE} (immutable, preserved).")
            sheets = read_excel_sheets(RAW_FILE)
        else:
            print("[acquire_data] Fixture mode: generating deterministic fixture (no genuine source required).")
            build_fixture()
            sheets = read_excel_sheets(RAW_FILE)
        manifest = build_manifest(sheets, RAW_FILE, source_type="synthetic_fixture", source_path=RAW_FILE)
        manifest["fixture_mode"] = True
        write_manifest(manifest)
        print(json.dumps(manifest, indent=2))
        return 0

    # Full mode: require the verified genuine UCI source at a distinct path.
    # Never download, never fall back to the synthetic fixture, never proceed silently.
    if not SOURCE_FILE.exists():
        err = (
            f"[acquire_data] FULL MODE BLOCKED: genuine UCI source not found at {SOURCE_FILE}\n"
            f"       Place the unmodified online_retail_II.xlsx at:\n"
            f"       {SOURCE_FILE}\n"
            f"       Then re-run: .venv\\Scripts\\python.exe run_pipeline.py --mode full\n"
            f"       Fixture mode remains available via: .venv\\Scripts\\python.exe run_pipeline.py --mode fixture"
        )
        print(err)
        write_download_instructions(err)
        return 1

    print(f"[acquire_data] Full mode: using verified genuine UCI source {SOURCE_FILE} (read-only input).")
    sheets = read_excel_sheets(SOURCE_FILE)
    manifest = build_manifest(sheets, SOURCE_FILE, source_type="genuine_uci", source_path=SOURCE_FILE)
    manifest["fixture_mode"] = False
    write_manifest(manifest)
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

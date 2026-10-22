"""Excel ingestor: read raw worksheets into a staged DataFrame with raw_row_id."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW_FILE = ROOT / "data" / "01_raw" / "online_retail_II.xlsx"
SHEET_2009_2010 = "Year 2009-2010"
SHEET_2010_2011 = "Year 2010-2011"

_COLUMN_RENAME = {
    "Price": "UnitPrice",
    "Customer ID": "CustomerID",
}


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename UCI CSV column names to the pipeline's canonical names.
    Label normalization only; data content is unchanged.
    """
    return df.rename(columns={k: v for k, v in _COLUMN_RENAME.items() if k in df.columns})


def _read_sheet(path: Path) -> tuple[str, pd.DataFrame]:
    """Read a single sheet (Excel) or whole CSV into a DataFrame.

    A file named .xlsx may actually hold CSV bytes; fall back to CSV reader.
    """
    try:
        xls = pd.ExcelFile(path)
        name = xls.sheet_names[0]
        df = pd.read_excel(xls, sheet_name=name, dtype={"Invoice": str, "StockCode": str})
        return name, df
    except Exception:
        df = pd.read_csv(path, dtype={"Invoice": str, "StockCode": str})
        df = _normalize_columns(df)
        return "Year 2009-2011", df


def ingest_raw(raw_file: Path = RAW_FILE) -> pd.DataFrame:
    """Read source worksheet(s) into a staged DataFrame with raw_row_id.

    raw_row_id = f"{sheet_index:02d}_{excel_row_number:07d}"
    where excel_row_number is the 1-based row in the sheet (header = row 1,
    first data row = row 2).
    """
    path = Path(raw_file)
    sheet_name, df = _read_sheet(path)
    if sheet_name is not None:
        # Single-sheet CSV source.
        df["source_sheet"] = sheet_name
        df["source_sheet_index"] = 1
        df["source_row_number"] = range(2, len(df) + 2)
        df["raw_row_id"] = [f"{1:02d}_{r:07d}" for r in range(2, len(df) + 2)]
        return df

    frames = []
    xls = pd.ExcelFile(raw_file)
    for sheet_index, name in enumerate(xls.sheet_names, start=1):
        df = pd.read_excel(xls, sheet_name=name, dtype={"Invoice": str, "StockCode": str})
        df["source_sheet"] = name
        df["source_sheet_index"] = sheet_index
        # excel row number: header occupies row 1; data starts at row 2
        df["source_row_number"] = range(2, len(df) + 2)
        df["raw_row_id"] = [
            f"{sheet_index:02d}_{r:07d}" for r in range(2, len(df) + 2)
        ]
        frames.append(df)
    staged = pd.concat(frames, ignore_index=True)
    return staged

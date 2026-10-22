"""Multiplicity-aware duplicate and worksheet overlap diagnostics.

Implements the 6-step protocol from the project specification:
  1. Traceable source identifier (raw_row_id)
  2. Worksheet date & overlap inspection
  3. Intra-sheet multiplicity tracking (same_sheet_occurrence_rank / count)
  4. Multiplicity-aware cross-sheet overlap detection
  5. Intra-sheet repetition & split-line diagnostics
  6. Three auditable reporting bases
"""
from __future__ import annotations

import pandas as pd

ROUND_DP = 4


def _norm_text(s: pd.Series) -> pd.Series:
    return (
        s.astype("string")
        .fillna("")
        .str.strip()
        .str.lower()
        .str.replace(r"\s+", " ", regex=True)
    )


def add_duplicate_diagnostics(df: pd.DataFrame) -> pd.DataFrame:
    """Add duplicate/multiplicity columns to a staged transactions DataFrame.

    Requires columns: Invoice, StockCode, Description, Quantity, InvoiceDate,
    UnitPrice, CustomerID, Country, source_sheet, raw_row_id.
    """
    df = df.copy()

    # Normalised signature components
    invoice = df["Invoice"].astype("string").fillna("")
    stock = df["StockCode"].astype("string").fillna("")
    desc = _norm_text(df.get("Description", pd.Series([""] * len(df))))
    qty = df["Quantity"].astype("float64")
    price = df["UnitPrice"].astype("float64").round(ROUND_DP)
    cust = _norm_text(df.get("CustomerID", pd.Series([""] * len(df))))
    country = _norm_text(df.get("Country", pd.Series([""] * len(df))))

    # Invoice date truncated to the minute for signature stability.
    if "InvoiceDate" in df.columns:
        inv_date = pd.to_datetime(df["InvoiceDate"], errors="coerce")
        inv_date_min = inv_date.dt.floor("min").astype(str).fillna("")
    else:
        inv_date_min = pd.Series([""] * len(df), index=df.index)

    df["line_signature"] = list(
        zip(invoice, stock, desc, qty, inv_date_min, price, cust, country)
    )

    # Step 3: intra-sheet occurrence rank & multiplicity (per worksheet).
    df = df.sort_values(["source_sheet_index", "source_row_number"]).reset_index(drop=True)
    grp = df.groupby("source_sheet")["line_signature"]
    df["same_sheet_occurrence_rank"] = grp.cumcount() + 1
    df["same_sheet_multiplicity_count"] = grp.transform("size")

    # Step 5a: same-sheet exact repeat
    df["is_same_sheet_exact_repeat"] = df["same_sheet_occurrence_rank"] > 1

    # Step 5b: same invoice + stock_code with different quantity/price -> split line
    split_mask = (
        df.groupby(["source_sheet", "Invoice", "StockCode"])["line_signature"]
        .transform("nunique")
        > 1
    )
    df["is_same_invoice_split_line"] = split_mask.fillna(False)

    # Step 4: cross-sheet overlap repeat (Sheet 2 row is a repeat if
    # (line_signature, same_sheet_occurrence_rank) exists in Sheet 1).
    sheet1_keys = set()
    mask_s1 = df["source_sheet_index"] == 1
    for key in df.loc[mask_s1, ["line_signature", "same_sheet_occurrence_rank"]].itertuples(
        index=False, name=None
    ):
        sheet1_keys.add(key)

    def is_cross(row) -> bool:
        if row["source_sheet_index"] != 2:
            return False
        return (row["line_signature"], int(row["same_sheet_occurrence_rank"])) in sheet1_keys

    df["is_cross_sheet_overlap_repeat"] = df.apply(is_cross, axis=1)

    # Store line_signature as a string for parquet/DuckDB portability.
    df["line_signature"] = df["line_signature"].map(str)

    # Reporting bases
    def reporting_basis(row) -> str:
        if row["is_cross_sheet_overlap_repeat"]:
            return "RAW_SOURCE_LEDGER_ONLY"
        if row["is_same_sheet_exact_repeat"]:
            return "OPERATIONAL_REPORTING_DEFAULT"
        return "STRICT_DISTINCT_SIGNATURE_SENSITIVITY"

    df["reporting_basis"] = df.apply(reporting_basis, axis=1)
    return df


def worksheet_overview(df: pd.DataFrame) -> pd.DataFrame:
    """Step 2: per-worksheet date range, row count, distinct invoice count."""
    rows = []
    for name, g in df.groupby("source_sheet"):
        rows.append(
            {
                "source_sheet": name,
                "row_count": int(len(g)),
                "distinct_invoice_count": int(g["Invoice"].nunique()) if "Invoice" in g.columns else None,
                "date_min": pd.to_datetime(g["InvoiceDate"], errors="coerce").min(),
                "date_max": pd.to_datetime(g["InvoiceDate"], errors="coerce").max(),
            }
        )
    return pd.DataFrame(rows)

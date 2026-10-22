"""Forensic classifier: monetary calculability, MECE categories, return-sign sub-classification."""
from __future__ import annotations

import pandas as pd

CAT_01 = "01_UNCALCULABLE_OR_MISSING_CORE"
CAT_02 = "02_ZERO_OR_NEGATIVE_UNIT_PRICE"
CAT_03 = "03_NON_MERCHANDISE_CHARGE_OR_FEE"
CAT_04 = "04_MERCHANDISE_CANCELLATION_OR_RETURN"
CAT_05 = "05_POSITIVE_MERCHANDISE_SALE"

# Verified non-merchandise stock codes (profiled empirically; see non_merchandise_code_evidence.csv)
NON_MERCHANDISE_CODES = {
    "POST", "DOT", "M", "BANK CHARGES", "B", "D", "CRUK", "C2", "PADS",
    "AMAZONFEE", "S", "ADJUST", "ADJUST2",
}


def _is_gift(s: pd.Series) -> pd.Series:
    return s.astype("string").fillna("").str.lower().str.startswith("gift_")


def classify(df: pd.DataFrame) -> pd.DataFrame:
    """Assign primary_audit_category, is_calculable_monetary, raw_signed_value,
    return_sign_subtype to a DataFrame that already has duplicate diagnostics."""
    df = df.copy()

    # --- Monetary calculability ---
    qty = pd.to_numeric(df["Quantity"], errors="coerce")
    price = pd.to_numeric(df["UnitPrice"], errors="coerce")
    df["is_calculable_monetary"] = qty.notna() & price.notna()
    df["raw_signed_value"] = None
    calc = df["is_calculable_monetary"]
    df.loc[calc, "raw_signed_value"] = (qty[calc] * price[calc]).round(2)

    # --- Normalised fields for classification ---
    invoice = df["Invoice"].astype("string").fillna("")
    stock = df["StockCode"].astype("string").fillna("")
    stock_norm = _norm_stock(stock)
    unit_price = price

    missing_core = (
        invoice.str.strip().eq("")
        | stock.str.strip().eq("")
        | df["InvoiceDate"].isna()
        | qty.isna()
        | price.isna()
        | (qty == 0)
    )

    # Category 01
    cat = pd.Series(CAT_01, index=df.index)
    not_01 = ~missing_core

    # Category 02: unit_price <= 0 (and not cat 01)
    is_02 = not_01 & unit_price.notna() & (unit_price <= 0)
    cat = cat.mask(is_02, CAT_02)
    not_02 = not_01 & ~is_02

    # Category 03: non-merchandise code (unit_price > 0, quantity != 0)
    is_03 = not_02 & stock_norm.isin(NON_MERCHANDISE_CODES) | _is_gift(df.get("Description", pd.Series([""] * len(df))))
    is_03 = is_03 & not_02
    cat = cat.mask(is_03, CAT_03)
    not_03 = not_02 & ~is_03

    # Category 04: invoice_no starts with 'C' OR quantity < 0 (unit_price > 0)
    is_04 = not_03 & (
        invoice.str.upper().str.startswith("C") | (qty < 0)
    )
    cat = cat.mask(is_04, CAT_04)
    not_04 = not_03 & ~is_04

    # Category 05: remainder
    cat = cat.mask(not_04, CAT_05)

    df["primary_audit_category"] = cat

    # --- Non-merchandise sub-classification (fee type / sign) ---
    df["fee_type"] = None
    fee_map = {
        "POST": "POSTAGE",
        "DOT": "DOT_CHARGE",
        "BANK CHARGES": "BANK_CHARGES",
        "AMAZONFEE": "AMAZON_FEE",
        "ADJUST": "ADJUSTMENT",
        "ADJUST2": "ADJUSTMENT_2",
    }
    df.loc[cat.eq(CAT_03), "fee_type"] = (
        df.loc[cat.eq(CAT_03), "StockCode"]
        .astype("string")
        .str.strip()
        .str.upper()
        .map(fee_map)
        .fillna("OTHER_FEE")
    )

    # --- Return-sign sub-classification for Category 04 ---
    df["return_sign_subtype"] = None
    is_c04 = cat.eq(CAT_04)
    signed = df["raw_signed_value"]

    c_inv_neg_qty = is_c04 & invoice.str.upper().str.startswith("C") & (qty < 0) & (signed < 0)
    non_c_inv_neg_qty = is_c04 & ~invoice.str.upper().str.startswith("C") & (qty < 0) & (signed < 0)
    anom_c_inv_pos_qty = is_c04 & invoice.str.upper().str.startswith("C") & (qty > 0) & (signed > 0)

    df.loc[c_inv_neg_qty, "return_sign_subtype"] = "C_INVOICE_NEGATIVE_QTY"
    df.loc[non_c_inv_neg_qty, "return_sign_subtype"] = "NON_C_INVOICE_NEGATIVE_QTY"
    df.loc[anom_c_inv_pos_qty, "return_sign_subtype"] = "ANOMALOUS_C_INVOICE_POSITIVE_QTY"
    # Category 04 rows that don't match the three sign patterns (defensive catch-all)
    unresolved = is_c04 & df["return_sign_subtype"].isna()
    df.loc[unresolved, "return_sign_subtype"] = "CATEGORY_04_OTHER"

    return df


def _norm_stock(s: pd.Series) -> pd.Series:
    return s.astype("string").fillna("").str.strip().str.upper()


def non_merchandise_evidence(df: pd.DataFrame) -> pd.DataFrame:
    """Profile non-standard stock_code values for evidence-backed classification."""
    stock = df["StockCode"].astype("string").fillna("")
    price = pd.to_numeric(df["UnitPrice"], errors="coerce")
    qty = pd.to_numeric(df["Quantity"], errors="coerce")
    signed = df.get("raw_signed_value", pd.Series([None] * len(df)))

    rows = []
    for code, g in df.groupby(stock):
        c = code.strip().upper()
        if c == "" or c.isdigit():
            continue
        rows.append(
            {
                "stock_code": c,
                "row_count": int(len(g)),
                "distinct_descriptions": int(g["Description"].astype("string").nunique()) if "Description" in g.columns else None,
                "sample_description": str(g["Description"].astype("string").iloc[0]) if len(g) and "Description" in g.columns else None,
                "positive_qty_rows": int((qty[g.index] > 0).sum()),
                "negative_qty_rows": int((qty[g.index] < 0).sum()),
                "zero_qty_rows": int((qty[g.index] == 0).sum()),
                "total_signed_gbp": round(float(signed[g.index].fillna(0).sum()), 2),
                "min_unit_price": float(price[g.index].min()) if price[g.index].notna().any() else None,
                "max_unit_price": float(price[g.index].max()) if price[g.index].notna().any() else None,
            }
        )
    ev = pd.DataFrame(rows)
    if len(ev):
        ev = ev.sort_values("row_count", ascending=False).reset_index(drop=True)
    return ev

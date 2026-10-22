"""Star schema builder: ingestion, classification, DuckDB star schema + analytics views."""
from __future__ import annotations

import sys
from pathlib import Path
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json

import duckdb
import pandas as pd

from ingestion.excel_ingestor import ingest_raw, RAW_FILE, SHEET_2009_2010, SHEET_2010_2011
from transformation.duplicate_diagnostics import add_duplicate_diagnostics, worksheet_overview
from transformation.forensic_classifier import (
    classify, non_merchandise_evidence, CAT_01, CAT_02, CAT_03, CAT_04, CAT_05,
)
from utils.config import get_project_config
from utils.db import connect, execute_sql_file
from utils.logger import get_logger

ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = ROOT / "data" / "02_processed"
PROCESSED_FILE = PROCESSED_DIR / "staged_transactions.parquet"
RECON_DIR = ROOT / "data" / "04_reconciliation"
EVIDENCE_FILE = RECON_DIR / "non_merchandise_code_evidence.csv"
DB_FILE = ROOT / "database" / "albion_analytics.duckdb"
SQL_DDL = ROOT / "sql" / "01_ddl" / "01_schemas_and_staging.sql"
SQL_TRANSFORMS = ROOT / "sql" / "02_transforms" / "02_empirical_star_schema.sql"
SQL_ANALYTICS = ROOT / "sql" / "03_analytics" / "03_commercial_and_customer_views.sql"
SQL_VALIDATION = ROOT / "sql" / "04_validation" / "04_reconciliation_assertions.sql"

logger = get_logger("transformation.star_schema_builder")


def load_staged() -> pd.DataFrame:
    if PROCESSED_FILE.exists():
        return pd.read_parquet(PROCESSED_FILE)
    # Determine which source file to read based on provenance manifest
    manifest_file = RECON_DIR / "provenance_manifest.json"
    if manifest_file.exists():
        manifest = json.loads(manifest_file.read_text())
        source_path = Path(manifest.get("source_path", str(RAW_FILE)))
    else:
        source_path = RAW_FILE
    df = ingest_raw(source_path)
    df = add_duplicate_diagnostics(df)
    df = classify(df)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(PROCESSED_FILE, index=False)
    return df


def build_evidence(df: pd.DataFrame) -> None:
    ev = non_merchandise_evidence(df)
    RECON_DIR.mkdir(parents=True, exist_ok=True)
    ev.to_csv(EVIDENCE_FILE, index=False)
    logger.info(f"Wrote non-merchandise evidence: {EVIDENCE_FILE} ({len(ev)} codes)")


def build_duckdb(df: pd.DataFrame) -> duckdb.DuckDBPyConnection:
    if DB_FILE.exists():
        DB_FILE.unlink()
    con = connect(DB_FILE)

    # Align DataFrame column order to the DDL table column order.
    ddl_cols = [
        "raw_row_id", "source_sheet", "source_sheet_index", "source_row_number",
        "Invoice", "StockCode", "Description", "Quantity", "InvoiceDate", "UnitPrice",
        "CustomerID", "Country", "line_signature", "same_sheet_occurrence_rank",
        "same_sheet_multiplicity_count", "is_same_sheet_exact_repeat",
        "is_same_invoice_split_line", "is_cross_sheet_overlap_repeat", "reporting_basis",
        "is_calculable_monetary", "raw_signed_value", "primary_audit_category",
        "fee_type", "return_sign_subtype",
    ]
    df = df[[c for c in ddl_cols if c in df.columns]]

    execute_sql_file(con, SQL_DDL)
    execute_sql_file(con, SQL_TRANSFORMS)

    # stg.raw_transactions - immutable full lineage
    con.register("staged_df", df)
    con.execute("INSERT INTO stg.raw_transactions SELECT * FROM staged_df")

    # core_empirical.classified_ledger - 1 row per raw_row_id
    con.execute(
        """
        INSERT INTO core_empirical.classified_ledger
        SELECT * FROM stg.raw_transactions
        """
    )

    # --- Dimensions ---
    # dim_date
    con.execute(
        """
        INSERT INTO mart_empirical.dim_date (date, year_month, year, quarter, month, day_name, is_weekend)
        SELECT CAST(d AS DATE) AS date,
               strftime(CAST(d AS DATE), '%Y-%m') AS year_month,
               EXTRACT(year FROM CAST(d AS DATE))::INTEGER AS year,
               EXTRACT(quarter FROM CAST(d AS DATE))::INTEGER AS quarter,
               EXTRACT(month FROM CAST(d AS DATE))::INTEGER AS month,
               strftime(CAST(d AS DATE), '%A') AS day_name,
               CASE WHEN EXTRACT(dow FROM CAST(d AS DATE)) IN (0,6) THEN 1 ELSE 0 END AS is_weekend
        FROM generate_series(DATE '2009-12-01', DATE '2011-12-31', INTERVAL 1 DAY) AS t(d)
        """
    )

    # dim_product (built cleanly below)
    con.execute("DELETE FROM mart_empirical.dim_product")
    con.execute(
        """
        INSERT INTO mart_empirical.dim_product
        SELECT
          stock_code,
          canonical_description,
          distinct_description_count,
          is_merchandise,
          first_sale_date,
          last_sale_date,
          median_unit_price
        FROM (
          SELECT
            UPPER(TRIM(StockCode)) AS stock_code,
            MIN(Description) AS canonical_description,
            COUNT(DISTINCT Description) AS distinct_description_count,
            MAX(CASE
                  WHEN UPPER(TRIM(StockCode)) IN ('POST','DOT','M','BANK CHARGES','B','D','CRUK','C2','PADS','AMAZONFEE','S','ADJUST','ADJUST2')
                   OR lower(Description) LIKE 'gift_%' THEN 0 ELSE 1 END) AS is_merchandise,
            MIN(InvoiceDate) AS first_sale_date,
            MAX(InvoiceDate) AS last_sale_date,
            QUANTILE_CONT(UnitPrice, 0.5) AS median_unit_price
          FROM stg.raw_transactions
          WHERE StockCode IS NOT NULL AND TRIM(StockCode) <> '' AND UnitPrice IS NOT NULL
          GROUP BY UPPER(TRIM(StockCode))
        ) t
        ORDER BY stock_code
        """
    )

    # dim_customer
    con.execute(
        """
        INSERT INTO mart_empirical.dim_customer
        SELECT
          cust_id AS customer_id,
          CASE WHEN cust_id = 'UNIDENTIFIED' THEN 'ANONYMOUS_GUEST' ELSE 'IDENTIFIED' END AS customer_status,
          MAX(Country) AS primary_country,
          MIN(InvoiceDate) AS first_order_date,
          MAX(InvoiceDate) AS last_order_date
        FROM (
          SELECT COALESCE(CAST(CustomerID AS VARCHAR), 'UNIDENTIFIED') AS cust_id, Country, InvoiceDate
          FROM stg.raw_transactions
          WHERE Invoice IS NOT NULL AND TRIM(Invoice) <> ''
        ) t
        GROUP BY cust_id
        """
    )

    # fact_merchandise_sales (category 05, not cross-sheet repeat)
    con.execute(
        """
        INSERT INTO mart_empirical.fact_merchandise_sales
        SELECT
          raw_row_id, source_sheet, Invoice AS invoice_no,
          UPPER(TRIM(StockCode)) AS stock_code, Description,
          Quantity AS quantity, InvoiceDate AS invoice_date,
          UnitPrice AS unit_price, raw_signed_value,
          CAST(CustomerID AS VARCHAR) AS customer_id, Country AS country
        FROM stg.raw_transactions
        WHERE primary_audit_category = '05_POSITIVE_MERCHANDISE_SALE'
          AND is_cross_sheet_overlap_repeat = FALSE
        """
    )

    # fact_returns_and_cancellations (category 04, not cross-sheet repeat)
    con.execute(
        """
        INSERT INTO mart_empirical.fact_returns_and_cancellations
        SELECT
          raw_row_id, source_sheet, Invoice AS invoice_no,
          UPPER(TRIM(StockCode)) AS stock_code, Description,
          Quantity AS quantity, InvoiceDate AS invoice_date,
          UnitPrice AS unit_price, raw_signed_value,
          return_sign_subtype,
          ABS(raw_signed_value) AS abs_return_value,
          CAST(CustomerID AS VARCHAR) AS customer_id, Country AS country
        FROM stg.raw_transactions
        WHERE primary_audit_category = '04_MERCHANDISE_CANCELLATION_OR_RETURN'
          AND is_cross_sheet_overlap_repeat = FALSE
        """
    )

    # fact_non_merch_and_adjustments (categories 01,02,03, not cross-sheet repeat)
    con.execute(
        """
        INSERT INTO mart_empirical.fact_non_merch_and_adjustments
        SELECT
          raw_row_id, source_sheet, Invoice AS invoice_no,
          UPPER(TRIM(StockCode)) AS stock_code, Description,
          Quantity AS quantity, InvoiceDate AS invoice_date,
          UnitPrice AS unit_price, raw_signed_value,
          primary_audit_category, return_sign_subtype,
          CAST(CustomerID AS VARCHAR) AS customer_id, Country AS country
        FROM stg.raw_transactions
        WHERE primary_audit_category IN ('01_UNCALCULABLE_OR_MISSING_CORE',
                                         '02_ZERO_OR_NEGATIVE_UNIT_PRICE',
                                         '03_NON_MERCHANDISE_CHARGE_OR_FEE')
          AND is_cross_sheet_overlap_repeat = FALSE
        """
    )

    # analytics views
    execute_sql_file(con, SQL_ANALYTICS)
    execute_sql_file(con, SQL_VALIDATION)

    con.close()
    logger.info(f"DuckDB built: {DB_FILE}")
    return connect(DB_FILE, read_only=True)


def run() -> int:
    cfg = get_project_config()
    logger.info("Starting star schema build")
    df = load_staged()
    logger.info(f"Staged transactions: {len(df):,} rows")
    build_evidence(df)
    build_duckdb(df)

    # Write a small reconciliation summary JSON for downstream reporting
    recon = {
        "total_rows": int(len(df)),
        "category_counts": df["primary_audit_category"].value_counts().to_dict(),
        "calculable_rows": int(df["is_calculable_monetary"].sum()),
        "uncalculable_rows": int((~df["is_calculable_monetary"]).sum()),
        "total_calculable_signed_gbp": round(float(df.loc[df["is_calculable_monetary"], "raw_signed_value"].sum()), 2),
        "cross_sheet_repeats": int(df["is_cross_sheet_overlap_repeat"].sum()),
        "same_sheet_repeats": int(df["is_same_sheet_exact_repeat"].sum()),
    }
    recon_file = RECON_DIR / "pipeline_reconciliation.json"
    recon_file.write_text(json.dumps(recon, indent=2), encoding="utf-8")
    logger.info(f"Reconciliation summary written: {recon_file}")
    print(json.dumps(recon, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(run())

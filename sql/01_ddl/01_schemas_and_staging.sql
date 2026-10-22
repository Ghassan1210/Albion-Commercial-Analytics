-- 01_schemas_and_staging.sql
-- Schemas and staging table for Albion Commercial Analytics (DuckDB).
-- Raw transactions are immutable: 1 row per raw_row_id with full lineage.

CREATE SCHEMA IF NOT EXISTS stg;
CREATE SCHEMA IF NOT EXISTS core_empirical;
CREATE SCHEMA IF NOT EXISTS mart_empirical;

DROP TABLE IF EXISTS stg.raw_transactions;
CREATE TABLE stg.raw_transactions (
    raw_row_id VARCHAR PRIMARY KEY,
    source_sheet VARCHAR,
    source_sheet_index INTEGER,
    source_row_number INTEGER,
    Invoice VARCHAR,
    StockCode VARCHAR,
    Description VARCHAR,
    Quantity DOUBLE,
    InvoiceDate TIMESTAMP,
    UnitPrice DOUBLE,
    CustomerID VARCHAR,
    Country VARCHAR,
    line_signature VARCHAR,
    same_sheet_occurrence_rank INTEGER,
    same_sheet_multiplicity_count INTEGER,
    is_same_sheet_exact_repeat BOOLEAN,
    is_same_invoice_split_line BOOLEAN,
    is_cross_sheet_overlap_repeat BOOLEAN,
    reporting_basis VARCHAR,
    is_calculable_monetary BOOLEAN,
    raw_signed_value DECIMAL(14,2),
    primary_audit_category VARCHAR,
    fee_type VARCHAR,
    return_sign_subtype VARCHAR
);

DROP TABLE IF EXISTS core_empirical.classified_ledger;
CREATE TABLE core_empirical.classified_ledger (
    raw_row_id VARCHAR PRIMARY KEY,
    source_sheet VARCHAR,
    source_sheet_index INTEGER,
    source_row_number INTEGER,
    Invoice VARCHAR,
    StockCode VARCHAR,
    Description VARCHAR,
    Quantity DOUBLE,
    InvoiceDate TIMESTAMP,
    UnitPrice DOUBLE,
    CustomerID VARCHAR,
    Country VARCHAR,
    line_signature VARCHAR,
    same_sheet_occurrence_rank INTEGER,
    same_sheet_multiplicity_count INTEGER,
    is_same_sheet_exact_repeat BOOLEAN,
    is_same_invoice_split_line BOOLEAN,
    is_cross_sheet_overlap_repeat BOOLEAN,
    reporting_basis VARCHAR,
    is_calculable_monetary BOOLEAN,
    raw_signed_value DECIMAL(14,2),
    primary_audit_category VARCHAR,
    fee_type VARCHAR,
    return_sign_subtype VARCHAR
);

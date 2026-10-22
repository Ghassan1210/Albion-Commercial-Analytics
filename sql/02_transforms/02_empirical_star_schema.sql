-- 02_empirical_star_schema.sql
-- Mart (star schema) tables. Built from stg.raw_transactions / core_empirical.classified_ledger.
-- This file is executed by the Python builder; tables are also populated there.

DROP TABLE IF EXISTS mart_empirical.dim_date;
CREATE TABLE mart_empirical.dim_date (
    date DATE PRIMARY KEY,
    year_month VARCHAR,
    year INTEGER,
    quarter INTEGER,
    month INTEGER,
    day_name VARCHAR,
    is_weekend INTEGER
);

DROP TABLE IF EXISTS mart_empirical.dim_product;
CREATE TABLE mart_empirical.dim_product (
    stock_code VARCHAR PRIMARY KEY,
    canonical_description VARCHAR,
    distinct_description_count INTEGER,
    is_merchandise INTEGER,
    first_sale_date DATE,
    last_sale_date DATE,
    median_unit_price DOUBLE
);

DROP TABLE IF EXISTS mart_empirical.dim_customer;
CREATE TABLE mart_empirical.dim_customer (
    customer_id VARCHAR PRIMARY KEY,
    customer_status VARCHAR,
    primary_country VARCHAR,
    first_order_date DATE,
    last_order_date DATE
);

DROP TABLE IF EXISTS mart_empirical.fact_merchandise_sales;
CREATE TABLE mart_empirical.fact_merchandise_sales (
    raw_row_id VARCHAR PRIMARY KEY,
    source_sheet VARCHAR,
    invoice_no VARCHAR,
    stock_code VARCHAR,
    Description VARCHAR,
    quantity DOUBLE,
    invoice_date TIMESTAMP,
    unit_price DOUBLE,
    raw_signed_value DECIMAL(14,2),
    customer_id VARCHAR,
    country VARCHAR
);

DROP TABLE IF EXISTS mart_empirical.fact_returns_and_cancellations;
CREATE TABLE mart_empirical.fact_returns_and_cancellations (
    raw_row_id VARCHAR PRIMARY KEY,
    source_sheet VARCHAR,
    invoice_no VARCHAR,
    stock_code VARCHAR,
    Description VARCHAR,
    quantity DOUBLE,
    invoice_date TIMESTAMP,
    unit_price DOUBLE,
    raw_signed_value DECIMAL(14,2),
    return_sign_subtype VARCHAR,
    abs_return_value DOUBLE,
    customer_id VARCHAR,
    country VARCHAR
);

DROP TABLE IF EXISTS mart_empirical.fact_non_merch_and_adjustments;
CREATE TABLE mart_empirical.fact_non_merch_and_adjustments (
    raw_row_id VARCHAR PRIMARY KEY,
    source_sheet VARCHAR,
    invoice_no VARCHAR,
    stock_code VARCHAR,
    Description VARCHAR,
    quantity DOUBLE,
    invoice_date TIMESTAMP,
    unit_price DOUBLE,
    raw_signed_value DECIMAL(14,2),
    primary_audit_category VARCHAR,
    return_sign_subtype VARCHAR,
    customer_id VARCHAR,
    country VARCHAR
);

DROP TABLE IF EXISTS mart_empirical.fact_audit_waterfall;
CREATE TABLE mart_empirical.fact_audit_waterfall (
    reporting_basis VARCHAR,
    primary_audit_category VARCHAR,
    total_rows BIGINT,
    calculable_rows BIGINT,
    uncalculable_rows BIGINT,
    calculable_signed_gbp DECIMAL(14,2)
);

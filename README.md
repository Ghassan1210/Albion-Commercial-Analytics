# Albion Commercial Analytics

Commercial Performance, Customer Intelligence and Inventory Optimization Engine.

**Case-study framing:** Albion is a fictional wrapper. The underlying transaction records are the authentic **UCI Machine Learning Repository — Online Retail II** dataset (Chen, D. 2012, CC BY 4.0, https://doi.org/10.24432/C5CG6D). The raw data did not originate from a real company called Albion.

## Repository
- `src/` — ingestion, transformation, analytics, simulation, reporting modules
- `sql/` — DuckDB DDL, transforms, analytics views, validation assertions
- `data/01_raw/` — immutable UCI raw dataset (excluded from git)
- `data/02_processed/` — staged parquet (excluded from git)
- `database/` — DuckDB database (excluded from git)
- `deliverables/` — Excel workbook, Power BI CSV package
- `docs/` — data dictionary, provenance, KPI definitions, methodology, executive summary, walkthrough, teacher demo script
- `tests/` — pytest suite
- `notebooks/` — executed Jupyter notebook

## Key Results (empirical)
{
  "category_reconciliation": [
    {
      "primary_audit_category": "02_ZERO_OR_NEGATIVE_UNIT_PRICE",
      "total_rows": 6207,
      "calculable_rows": 6207,
      "uncalculable_rows": 0,
      "calculable_signed_gbp": -158676.14
    },
    {
      "primary_audit_category": "03_NON_MERCHANDISE_CHARGE_OR_FEE",
      "total_rows": 5783,
      "calculable_rows": 5783,
      "uncalculable_rows": 0,
      "calculable_signed_gbp": 60374.97
    },
    {
      "primary_audit_category": "04_MERCHANDISE_CANCELLATION_OR_RETURN",
      "total_rows": 18290,
      "calculable_rows": 18290,
      "uncalculable_rows": 0,
      "calculable_signed_gbp": -726611.45
    },
    {
      "primary_audit_category": "05_POSITIVE_MERCHANDISE_SALE",
      "total_rows": 1037091,
      "calculable_rows": 1037091,
      "uncalculable_rows": 0,
      "calculable_signed_gbp": 20112163.17
    }
  ],
  "total_calculable_raw_signed_gbp": 19287250.55,
  "positive_merchandise_sales_gbp": 20112163.17,
  "cat04_signed_return_and_cancellation_gbp": -726611.45,
  "cat04_negative_return_signed_gbp": -726611.45,
  "recorded_return_and_cancellation_magnitude_gbp": 726611.45,
  "cat04_positive_cancellation_anomaly_gbp": 0.0,
  "net_recorded_merchandise_value_gbp": 19385551.72,
  "merchandise_return_rate_pct": 0.036128,
  "non_merchandise_net_value_gbp": -98301.17,
  "identified_customer_revenue_gbp": 17434690.73,
  "anonymous_guest_revenue_gbp": 2677472.44,
  "identified_customer_revenue_share_pct": 86.6873
}

## Simulation (SIMULATED_HYBRID — configured assumptions, not empirical)
[
  {
    "scenario": "S1_BASELINE",
    "sim_sku_count": 4733,
    "sim_total_working_capital_gbp": 3016637.5,
    "sim_total_annual_inventory_cost_gbp": 1098476.74,
    "sim_avg_eoq_units": 982.0412085358124,
    "sim_avg_safety_stock_units": 208.91233044580605,
    "sim_avg_reorder_point_units": 379.09300654975704
  },
  {
    "scenario": "S2_LEAD_TIME_SHOCK_PLUS_50PCT",
    "sim_sku_count": 4733,
    "sim_total_working_capital_gbp": 3300148.06,
    "sim_total_annual_inventory_cost_gbp": 1160848.79,
    "sim_avg_eoq_units": 982.0412085358124,
    "sim_avg_safety_stock_units": 265.2901986055356,
    "sim_avg_reorder_point_units": 520.5613395309529
  },
  {
    "scenario": "S3_COST_INFLATION_PLUS_15PCT",
    "sim_sku_count": 4733,
    "sim_total_working_capital_gbp": 3184490.12,
    "sim_total_annual_inventory_cost_gbp": 1293188.0,
    "sim_avg_eoq_units": 859.0573315022185,
    "sim_avg_safety_stock_units": 208.91233044580605,
    "sim_avg_reorder_point_units": 379.09300654975704
  }
]

## Reproduction
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
python run_pipeline.py
pytest tests/ -v

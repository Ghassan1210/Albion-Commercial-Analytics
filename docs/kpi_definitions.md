# KPI Definitions
- positive_merchandise_sales_gbp: SUM(raw_signed_value) for category 05_POSITIVE_MERCHANDISE_SALE
- cat04_signed_return_and_cancellation_gbp: net signed SUM(raw_signed_value) for category 04
- cat04_negative_return_signed_gbp: SUM(raw_signed_value) where raw_signed_value < 0 in cat 04
- recorded_return_and_cancellation_magnitude_gbp: ABS(cat04_negative_return_signed_gbp)
- cat04_positive_cancellation_anomaly_gbp: SUM(raw_signed_value) where raw_signed_value > 0 in cat 04
- net_recorded_merchandise_value_gbp: positive_merchandise_sales_gbp + cat04_signed_return_and_cancellation_gbp
- merchandise_return_rate_pct: recorded_return_and_cancellation_magnitude_gbp / positive_merchandise_sales_gbp

Computed values: {
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

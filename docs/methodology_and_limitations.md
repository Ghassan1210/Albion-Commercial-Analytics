# Methodology & Limitations
- Multiplicity-aware duplicate protocol preserves intra-sheet exact repeats; only cross-sheet overlap repeats are excluded from operational reporting.
- Monetary calculability: raw_signed_value is NULL where quantity or unit_price is missing; never coerced to zero.
- MECE categories 01-05 with strict precedence.
- Return-sign convention validated empirically (C-invoice negative qty, non-C negative qty, positive C anomalies reported).
- Inventory simulation is SIMULATED_HYBRID (configured assumptions), not empirical.
- Observational price-quantity analysis makes no causal claims.

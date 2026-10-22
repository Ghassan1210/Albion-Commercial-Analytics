# Final Project Closeout Report

## Scope

This closeout records the current verified state of Albion Commercial Analytics. The supplied Power BI Desktop result block contained placeholders rather than observed values, so Desktop refresh and rendering are explicitly marked **unverified**.

## Confirmed artifacts

- PBIX: `deliverables/powerbi/Albion_Commercial_Analytics.pbix`
  - Size: 22,685,598 bytes
  - SHA-256: `DCD0423CA00D2198159D1E6C04BBB3B6E9427C2BCB0539FF10FE56A64E87D0FF`
  - Verified as a ZIP-based PBIX archive with five report pages and 21 visual definitions.
- Editable PBIP: `deliverables/powerbi/Albion_Commercial_Analytics_Project/Albion_Commercial_Analytics.pbip`
  - SHA-256: `0FC267136BFB913883B54A196C987963746A08B5C887EF0EA66313A1C8D689A8`
- Excel workbook exists at `deliverables/excel/Albion_Commercial_Analytics.xlsx`.

## Data and model evidence

- Eight exports and expected row counts were previously verified.
- Current validation report records genuine UCI provenance (`source_type=genuine_uci`, `fixture_mode=false`, `total_rows=1,067,371`).
- Controls recorded in the report are: merchandise £20,112,163.17; returns absolute magnitude £726,611.45; net merchandise £19,385,551.72; non-merchandise net −£98,301.17; total calculable signed value £19,287,250.55.
- The corrected measure is `Sim Working Capital GBP := SUM(sim_inventory_sku_scenarios[sim_working_capital_gbp])`. No historical date or `fact_inventory` reference remains in the generator or DAX library.
- Simulated inventory values remain scenario outputs and are not historical transactions.

## Validation commands

- `\.venv\Scripts\python.exe -m pytest tests -q` — **31 passed**, exit code 0.
- JSON parse of `data/04_reconciliation/final_validation_report.json` — **passed**.
- Local `main` and `origin/main` both point to `ed09722c02456d5561d8d664f9125c3a0df1a0d2`.

## Power BI Desktop status

The supplied Desktop evidence fields were not populated with an actual warning, refresh result, affected query, or page results. Consequently:

- PBIX opened: **not evidenced in this pass**.
- Refresh: **not evidenced in this pass**.
- Five-page rendering: **not evidenced in this pass**.
- Incomplete/no-data warning: **status unresolved**.

The PBIP source contains the intended eight-table model, nine relationships, twelve measures, and five report pages. Static validation cannot substitute for an observed Desktop refresh.

## Remaining action

Open the active PBIX/PBIP in Power BI Desktop, perform one controlled Refresh, and record the exact result. If an error appears, capture the affected query/table and exact message so the remaining issue can be repaired from evidence.

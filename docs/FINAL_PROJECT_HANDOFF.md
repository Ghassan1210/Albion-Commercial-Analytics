# Final Project Handoff

## Current release state

The project has a verified genuine-data analytical package and a saved PBIX candidate. The editable source is the PBIP project under `deliverables/powerbi/Albion_Commercial_Analytics_Project/`; the saved report is `deliverables/powerbi/Albion_Commercial_Analytics.pbix`.

The PBIX is 22,685,598 bytes with SHA-256 `DCD0423CA00D2198159D1E6C04BBB3B6E9427C2BCB0539FF10FE56A64E87D0FF`. The PBIP SHA-256 is `0FC267136BFB913883B54A196C987963746A08B5C887EF0EA66313A1C8D689A8`.

## Source and model handoff

The current source exports, eight-table model, nine intended relationships, and twelve approved measures are preserved. The working-capital measure is scenario-grain based:

```DAX
Sim Working Capital GBP := SUM(sim_inventory_sku_scenarios[sim_working_capital_gbp])
```

It must be presented as simulated inventory scenario analysis, not historical performance.

## Evidence completed

- Genuine UCI provenance and validation report regenerated.
- Expected export counts and financial controls verified in existing evidence.
- 31 tests passed with exit code 0.
- Validation report JSON parsed successfully.
- Local `main` equals `origin/main` at `ed09722c02456d5561d8d664f9125c3a0df1a0d2`.

## Desktop handoff requirement

No populated Desktop test result was supplied in the final request. Do not claim that refresh, page rendering, or the incomplete-data warning has been resolved until Power BI Desktop provides an observed result. Perform one refresh, capture any exact error, and use that evidence for the final release decision.

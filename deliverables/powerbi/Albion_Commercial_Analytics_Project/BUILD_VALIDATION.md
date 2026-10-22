# Albion Commercial Analytics PBIP build validation

## Generated

- `Albion_Commercial_Analytics.pbip` points to the sibling report folder.
- `Albion_Commercial_Analytics.SemanticModel/definition.pbism` declares semantic model version 4.2.
- The semantic model uses TMDL under `definition/` with eight CSV-backed import tables and `relationships.tmdl` containing the nine documented active, single-direction relationships.
- `Albion_Commercial_Analytics.Report/definition.pbir` uses a relative `byPath` reference to the semantic model.
- PBIR contains five pages: Executive Overview, Sales Performance, Product & Customer Intelligence, Returns & Reconciliation, and Inventory Scenario Analysis.

## TMDL repair

- Fixed the reported `InvalidLineType: ReferenceObject` error in `definition/model.tmdl` by moving all eight `ref table ...` declarations to the TMDL root level, while keeping model properties indented beneath `model Model`.
- A complete pre-repair backup is available at `../Albion_Commercial_Analytics_Project_backup_before_tmdl_repair/`.

## Local validation completed

- All eight generated JSON files parsed successfully with PowerShell `ConvertFrom-Json`.
- All eight Power Query M partitions point to the existing absolute CSV folder:
  `C:\Important GHN files\GHN12\deliverables\powerbi\data_model_exports\`.
- Table names and column names were checked against the current export schemas and approved DAX library.
- Relationship validation found all nine relationship endpoints in the eight table definitions; dimension-side keys are the documented one-side keys and filter behavior is `oneDirection`.
- All 12 intended measures are present in the table TMDL files and their referenced columns/measures exist in the generated model definitions.
- Documented control totals: merchandise 1,037,091 rows / £20,112,163.17; returns 18,290 rows / £726,611.45; remaining exports 761, 5,131, 5,943, 11,990, 9, and 14,199 rows respectively.

## Desktop validation still required

Power BI Desktop was asked to open the PBIP, but this session has no supported Desktop UI or model-engine validation surface. The process remained responsive, but the report title did not change from `Untitled - Power BI Desktop`; therefore successful loading, TMDL parsing, refresh, visual rendering, and PBIX save are not claimed here.

The Executive Overview contains four approved-measure cards and one monthly sales line visual using documented model fields. The other four priority pages are structurally present and ready for additional visuals from the checklist. After opening the PBIP, apply/refresh the model, confirm the Executive Overview visuals, add the remaining approved measures if needed, and create the remaining page visuals. Save as `..\\Albion_Commercial_Analytics.pbix`.

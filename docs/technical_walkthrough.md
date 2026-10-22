# Technical Walkthrough
1. acquire_data.py downloads/extracts UCI xlsx; records provenance manifest.
2. excel_ingestor.py reads both sheets; assigns raw_row_id.
3. duplicate_diagnostics.py adds multiplicity & overlap flags.
4. forensic_classifier.py adds monetary calculability + MECE categories + return-sign subtypes.
5. star_schema_builder.py writes parquet + DuckDB star schema + analytics views.
6. analytics modules compute KPIs, RFM, ABC-XYZ, price-quantity, seasonal forecast.
7. simulation module computes 3 inventory scenarios.
8. reporting modules build notebook, Excel, Power BI package, docs.

# Teacher Demo Script
1. Open `notebooks/01_albion_commercial_and_inventory_analysis.ipynb` and run all cells.
2. Review `deliverables/excel/Albion_Commercial_Analytics.xlsx` (10 sheets).
3. Inspect `deliverables/powerbi/data_model_exports/` CSVs and `DAX_Measures_Library.dax`.
4. Run `pytest tests/ -v` to verify.
5. Re-run `python run_pipeline.py` to confirm idempotency.
Key talking point: distinguish [EMPIRICAL] (UCI data) from [SIMULATED_HYBRID] (inventory simulation).

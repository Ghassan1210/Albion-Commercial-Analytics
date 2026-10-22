"""Albion Commercial Analytics - idempotent CLI entry point.

Runs the full Milestone A->E pipeline (or a fixture-only verification when the
UCI dataset cannot be downloaded) without duplicating rows or corrupting outputs.

Usage:
    python run_pipeline.py                    # full pipeline
    python run_pipeline.py --mode fixture     # deterministic fixture-only verification
    python run_pipeline.py --skip-tests       # run pipeline, skip pytest
    python run_pipeline.py --tests-only       # run pytest only
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def run_module(module: str, *args: str) -> int:
    print(f"\n{'='*70}\nRUN: python -m {module} {' '.join(args)}\n{'='*70}")
    env = dict(__import__("os").environ)
    env["PYTHONPATH"] = str(SRC) + (";" + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    return subprocess.run([sys.executable, "-m", module, *args], cwd=ROOT, env=env).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Albion Commercial Analytics pipeline")
    parser.add_argument("--mode", choices=["full", "fixture"], default="full",
                        help="full = download/process UCI dataset; fixture = deterministic test fixture only")
    parser.add_argument("--skip-tests", action="store_true", help="skip pytest execution")
    parser.add_argument("--tests-only", action="store_true", help="run pytest only")
    args = parser.parse_args()

    if args.tests_only:
        return subprocess.run([sys.executable, "-m", "pytest", "tests", "-v"], cwd=ROOT).returncode

    rc = 0
    # Milestone A: data acquisition
    rc = run_module("ingestion.acquire_data", "--mode", args.mode)
    if rc != 0:
        print("Milestone A (data acquisition) failed.")
        return rc

    # Milestone B: ingestion, classification, DuckDB star schema
    rc = run_module("transformation.star_schema_builder")
    if rc != 0:
        print("Milestone B (transformation / star schema) failed.")
        return rc

    # Milestone C: analytics + simulation
    rc = run_module("analytics.commercial_metrics")
    if rc != 0:
        print("Milestone C (commercial metrics) failed.")
        return rc
    rc = run_module("analytics.customer_intelligence")
    if rc != 0:
        print("Milestone C (customer intelligence) failed.")
        return rc
    rc = run_module("analytics.product_demand_abc_xyz")
    if rc != 0:
        print("Milestone C (product demand ABC-XYZ) failed.")
        return rc
    rc = run_module("analytics.price_quantity_analysis")
    if rc != 0:
        print("Milestone C (price quantity analysis) failed.")
        return rc
    rc = run_module("analytics.seasonal_forecasting")
    if rc != 0:
        print("Milestone C (seasonal forecasting) failed.")
        return rc
    rc = run_module("simulation.inventory_working_capital_sim")
    if rc != 0:
        print("Milestone C (inventory simulation) failed.")
        return rc

    # Milestone D: reporting deliverables
    rc = run_module("reporting.notebook_builder")
    if rc != 0:
        print("Milestone D (notebook builder) failed.")
        return rc
    rc = run_module("reporting.excel_workbench")
    if rc != 0:
        print("Milestone D (excel workbench) failed.")
        return rc
    rc = run_module("reporting.powerbi_package")
    if rc != 0:
        print("Milestone D (powerbi package) failed.")
        return rc
    rc = run_module("reporting.documentation_builder")
    if rc != 0:
        print("Milestone D (documentation builder) failed.")
        return rc

    # Milestone E: pytest verification
    if not args.skip_tests:
        rc = subprocess.run([sys.executable, "-m", "pytest", "tests", "-v"], cwd=ROOT).returncode
        if rc != 0:
            print("Milestone E (pytest) reported failures.")
            return rc

    print("\nPipeline completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

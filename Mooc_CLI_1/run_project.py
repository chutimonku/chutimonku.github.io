#!/usr/bin/env python3
"""Single reproducible entry point for the authoritative Workflow.md."""
from src.workflow import run_all

if __name__ == "__main__":
    result = run_all()
    print(f"Workflow completed: {result['status']} in {result['elapsed_seconds']:.1f}s")
    print("Report: reports/mooc_data_science_report.html")
    print("Verification: outputs/reproducibility/artifact_check.json")

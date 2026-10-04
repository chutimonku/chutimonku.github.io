"""Compatibility entry point for acquisition, quality, splitting, and EDA."""
from src.workflow import run_data_stage

if __name__ == "__main__":
    print(run_data_stage())

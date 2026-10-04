import pytest
import pandas as pd
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

def test_raw_dataset_exists_and_shape():
    path = ROOT_DIR / "data" / "raw" / "dataset.csv"
    assert path.exists(), "Raw dataset must exist."
    df = pd.read_csv(path)
    assert df.shape == (149, 25), "Raw dataset must have exactly 149 rows and 25 columns."

def test_target_quarantine_integrity():
    q_path = ROOT_DIR / "data" / "quarantine" / "target.csv"
    if not q_path.exists():
        q_path = ROOT_DIR / "data" / "raw_quarantine" / "target.csv"
    assert q_path.exists(), "Quarantined target file must exist."
    df_q = pd.read_csv(q_path)
    assert "claims_paid_ratio_no" in df_q.columns
    assert len(df_q) == 149

def test_ratio_mathematical_consistency():
    df = pd.read_csv(ROOT_DIR / "data" / "raw" / "dataset.csv")
    valid = df[(df['total_claims_no'] > 0) & (df['life_insurer'] != 'Sahara Life')]
    calculated = valid['claims_paid_no'] / valid['total_claims_no']
    diff = (calculated - valid['claims_paid_ratio_no']).abs()
    assert diff.max() < 1e-4, "Except for Sahara Life, calculated ratio must match reported ratio."

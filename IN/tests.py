import pandas as pd
import numpy as np
import pytest
import os
import json
import joblib
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent

def test_raw_data_integrity():
    df = pd.read_csv(ROOT_DIR / "data" / "raw" / "dataset.csv")
    assert df.shape == (149, 25), "Raw dataset should be unchanged."

def test_ratio_logic():
    df = pd.read_csv(ROOT_DIR / "data" / "raw" / "dataset.csv")
    valid = df[df['total_claims_no'] > 0]
    valid = valid[valid['life_insurer'] != 'Sahara Life']
    calculated = valid['claims_paid_no'] / valid['total_claims_no']
    diff = (calculated - valid['claims_paid_ratio_no']).abs()
    assert diff.max() < 1e-4

def test_temporal_split():
    split_file = ROOT_DIR / "outputs" / "evaluation" / "split_summary.json"
    if not split_file.exists():
        pytest.skip("split_summary.json does not exist yet")
    with open(split_file) as f:
        splits = json.load(f)
    assert "train" in splits
    assert "val" in splits or "validation" in splits
    assert "test" in splits

def test_schema_validation():
    schema_file = ROOT_DIR / "models" / "final" / "schema.json"
    if not schema_file.exists():
        pytest.skip("schema.json does not exist yet")
    with open(schema_file) as f:
        schema = json.load(f)
    assert "features" in schema
    assert "validation_results" in schema

def test_pipeline_artifact():
    artifact_path = ROOT_DIR / "models" / "final" / "rf_model_final.pkl"
    if artifact_path.exists():
        model = joblib.load(artifact_path)
        assert hasattr(model, "predict"), "Artifact should be a valid scikit-learn estimator/pipeline."

def test_quarantine_target_exists():
    q1 = ROOT_DIR / "data" / "quarantine" / "target.csv"
    q2 = ROOT_DIR / "data" / "raw_quarantine" / "target.csv"
    assert q1.exists() or q2.exists()

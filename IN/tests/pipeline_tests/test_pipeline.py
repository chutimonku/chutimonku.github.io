import pytest
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

def test_temporal_split_structure():
    split_file = ROOT_DIR / "outputs" / "evaluation" / "split_summary.json"
    if not split_file.exists():
        pytest.skip("split_summary.json not generated yet")
    with open(split_file) as f:
        splits = json.load(f)
    assert "train" in splits
    assert "val" in splits or "validation" in splits
    assert "test" in splits
    assert splits["test"] > 0

def test_schema_json_contract():
    schema_file = ROOT_DIR / "models" / "final" / "schema.json"
    if not schema_file.exists():
        pytest.skip("schema.json not generated yet")
    with open(schema_file) as f:
        schema = json.load(f)
    assert "features" in schema
    assert "validation_results" in schema

def test_cleaning_audit_log():
    audit_file = ROOT_DIR / "logs" / "cleaning_audit.json"
    if not audit_file.exists():
        pytest.skip("cleaning_audit.json not generated yet")
    with open(audit_file) as f:
        audit = json.load(f)
    assert isinstance(audit, list)
    assert len(audit) >= 2

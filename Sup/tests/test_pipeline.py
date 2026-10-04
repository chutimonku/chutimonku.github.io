"""Test suite for MOOC student risk prediction deployment pipeline."""

import os
import joblib
import numpy as np
import pandas as pd
import pytest
from src.deployment import DataLeakageSecurityException, InputSchemaError, MoocStudentRiskPipeline

PIPELINE_PATH = os.path.join("models", "final", "deployment_pipeline.joblib")


@pytest.fixture
def loaded_pipeline():
    if not os.path.exists(PIPELINE_PATH):
        pytest.skip(f"Pipeline artifact {PIPELINE_PATH} not found. Run workflow first.")
    return joblib.load(PIPELINE_PATH)


@pytest.fixture
def valid_student_df(loaded_pipeline):
    source = pd.read_parquet("data/processed/students_cleaned.parquet")
    columns = ["userid_DI", *loaded_pipeline.required_input_features]
    frame = source.loc[source.index[:2], columns].copy()
    frame["userid_DI"] = ["TEST_STUDENT_01", "TEST_STUDENT_02"]
    return frame


def test_pipeline_instance(loaded_pipeline):
    assert isinstance(loaded_pipeline, MoocStudentRiskPipeline)
    assert hasattr(loaded_pipeline, "predict_proba")
    assert hasattr(loaded_pipeline, "predict")
    assert hasattr(loaded_pipeline, "predict_risk_tiers")


def test_batch_prediction(loaded_pipeline, valid_student_df):
    results = loaded_pipeline.predict_risk_tiers(valid_student_df)
    assert len(results) == 2
    assert "completion_probability" in results.columns
    assert "risk_tier" in results.columns
    assert "recommended_support_action" in results.columns
    assert (results["completion_probability"] >= 0.0).all()
    assert (results["completion_probability"] <= 1.0).all()


def test_single_student_prediction(loaded_pipeline, valid_student_df):
    single_df = valid_student_df.iloc[[0]]
    probs = loaded_pipeline.predict_proba(single_df)
    assert len(probs) == 1
    assert 0.0 <= probs[0] <= 1.0


def test_anti_leakage_exception_certified(loaded_pipeline, valid_student_df):
    leaked_df = valid_student_df.copy()
    leaked_df["certified"] = [0, 1]
    with pytest.raises(DataLeakageSecurityException):
        loaded_pipeline.predict_risk_tiers(leaked_df)


def test_anti_leakage_exception_grade(loaded_pipeline, valid_student_df):
    leaked_df = valid_student_df.copy()
    leaked_df["grade"] = [0.0, 0.85]
    with pytest.raises(DataLeakageSecurityException):
        loaded_pipeline.predict_proba(leaked_df)


def test_anti_leakage_exception_explored(loaded_pipeline, valid_student_df):
    leaked_df = valid_student_df.copy()
    leaked_df["explored"] = [0, 1]
    with pytest.raises(DataLeakageSecurityException):
        loaded_pipeline.predict(leaked_df)


def test_missing_required_column(loaded_pipeline, valid_student_df):
    # Mean/max aggregates cannot be reconstructed from headline totals and must
    # never be replaced silently with zero.
    bad_df = valid_student_df.drop(columns=["mean_events_per_course"])
    with pytest.raises(InputSchemaError):
        loaded_pipeline.predict_risk_tiers(bad_df)


def test_duplicate_student_id(loaded_pipeline, valid_student_df):
    dup_df = pd.concat([valid_student_df, valid_student_df.iloc[[0]]], ignore_index=True)
    with pytest.raises(InputSchemaError):
        loaded_pipeline.predict_risk_tiers(dup_df)


def test_negative_activity_value(loaded_pipeline, valid_student_df):
    neg_df = valid_student_df.copy()
    neg_df.loc[0, "total_events"] = -10
    with pytest.raises(InputSchemaError):
        loaded_pipeline.predict_risk_tiers(neg_df)


def test_unseen_categorical_robustness(loaded_pipeline, valid_student_df):
    unseen_df = valid_student_df.copy()
    unseen_df["country"] = "Fictional Land"
    unseen_df["LoE_DI"] = "Post-Doc Specialized Fellowship"
    unseen_df["gender"] = "non-binary-custom"
    # Pipeline should handle unseen categories via OneHotEncoder(handle_unknown='ignore')
    results = loaded_pipeline.predict_risk_tiers(unseen_df)
    assert len(results) == 2
    assert (results["completion_probability"] >= 0.0).all()


if __name__ == "__main__":
    pytest.main(["-v", __file__])

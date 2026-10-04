import pytest
import joblib
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

def test_final_model_artifacts_loadable():
    rf_path = ROOT_DIR / "models" / "final" / "rf_model_final.pkl"
    if not rf_path.exists():
        pytest.skip("rf_model_final.pkl not generated yet")
    model = joblib.load(rf_path)
    assert hasattr(model, "predict"), "Final model must have a predict method."

def test_clustering_pipeline_artifact():
    cluster_path = ROOT_DIR / "models" / "final" / "clustering_pipeline.joblib"
    if not cluster_path.exists():
        pytest.skip("clustering_pipeline.joblib not generated yet")
    cluster_bundle = joblib.load(cluster_path)
    assert "model" in cluster_bundle
    assert "scaler" in cluster_bundle
    assert "selected_k" in cluster_bundle
    assert cluster_bundle["selected_k"] >= 2

def test_forecast_bundle_artifact():
    forecast_path = ROOT_DIR / "models" / "final" / "forecast_bundle.joblib"
    if not forecast_path.exists():
        pytest.skip("forecast_bundle.joblib not generated yet")
    forecast_bundle = joblib.load(forecast_path)
    assert "decision_champion" in forecast_bundle
    assert "challenger_pipeline" in forecast_bundle

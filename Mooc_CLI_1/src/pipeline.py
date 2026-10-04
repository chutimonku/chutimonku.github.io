"""Load and use the locked classification and clustering pipelines."""
import joblib
import pandas as pd

from src.workflow import CLASS_FEATURES, FINAL_MODELS, StudentClusteringPipeline

def load_classification_pipeline():
    return joblib.load(FINAL_MODELS / "classification_pipeline.joblib")

def load_clustering_pipeline() -> StudentClusteringPipeline:
    return joblib.load(FINAL_MODELS / "clustering_pipeline.joblib")

def predict_certification(frame: pd.DataFrame) -> pd.DataFrame:
    forbidden = sorted({"grade", "explored", "incomplete_flag"} & set(frame.columns))
    if forbidden:
        raise ValueError(f"Leakage columns forbidden at inference: {forbidden}")
    missing = sorted(set(CLASS_FEATURES) - set(frame.columns))
    if missing:
        raise ValueError(f"Missing classification features: {missing}")
    model = load_classification_pipeline()
    score = model.predict_proba(frame[CLASS_FEATURES])[:, 1]
    return pd.DataFrame({"certification_score": score, "prediction": (score >= .5).astype(int)}, index=frame.index)

def predict_clusters(frame: pd.DataFrame) -> pd.DataFrame:
    model = load_clustering_pipeline()
    return pd.DataFrame({"cluster": model.predict(frame)}, index=frame.index)

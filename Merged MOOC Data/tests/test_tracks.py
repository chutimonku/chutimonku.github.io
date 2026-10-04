"""Verification tests for the active multi-track workflow."""

import json
import os

import joblib
import pandas as pd


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def path(*parts):
    return os.path.join(ROOT, *parts)


def load_json(*parts):
    with open(path(*parts), encoding="utf-8") as handle:
        return json.load(handle)


def test_unsupervised_features_are_selected_from_clean_merged_data():
    manifest = load_json("outputs", "reproducibility", "unsupervised_track_manifest.json")
    registry = pd.read_csv(path("outputs", "tables", "feature_registry.csv"))
    selected = registry.loc[registry["unsupervised_selected"], "feature"].tolist()
    assert manifest["feature_count"] == len(selected) >= 2
    assert set(manifest["input_features"]) == set(selected)
    assert all(feature.startswith("mean_course_") and feature.endswith("_percentile") for feature in selected)
    assert not {"certified", "grade", "viewed", "explored"}.intersection(manifest["input_features"])


def test_k_is_data_selected_and_all_students_are_assigned():
    manifest = load_json("outputs", "reproducibility", "unsupervised_track_manifest.json")
    comparison = pd.read_csv(path("outputs", "tables", "unsupervised_model_comparison.csv"))
    assignments = pd.read_csv(path("outputs", "data", "unsupervised_cluster_assignments.csv"))
    assert manifest["k_values_evaluated"] == list(range(2, 11))
    assert comparison["selected"].sum() == 1
    assert len(assignments) == assignments["userid_DI"].nunique() == 446_766
    assert assignments["unsupervised_cluster"].nunique() == manifest["selected_k"]


def test_supervised_feature_contract_and_test_metrics():
    manifest = load_json("outputs", "reproducibility", "supervised_track_manifest.json")
    results = pd.read_csv(path("outputs", "tables", "supervised_model_comparison.csv"))
    spec = pd.read_csv(path("outputs", "tables", "supervised_feature_specification.csv"))
    transformed = pd.read_csv(path("outputs", "tables", "supervised_transformed_features.csv"))
    assert manifest["source_feature_count"] == len(spec)
    assert manifest["transformed_feature_count"] == len(transformed)
    assert manifest["students"] >= 1
    assert results["selected"].sum() == 1
    for column in ["test_accuracy", "test_balanced_accuracy", "test_precision", "test_recall", "test_f1", "runtime_sec"]:
        assert results[column].notna().all()


def test_deep_learning_is_classification_not_clustering():
    manifest = load_json("outputs", "reproducibility", "deep_learning_track_manifest.json")
    results = pd.read_csv(path("outputs", "tables", "deep_learning_model_comparison.csv"))
    predictions = pd.read_csv(path("outputs", "data", "deep_certification_predictions.csv"))
    assert manifest["task_type"] == "supervised classification"
    assert "selected_k" not in manifest
    assert results["selected"].sum() == 1
    assert {"test_pr_auc", "test_accuracy", "test_f1"}.issubset(results.columns)
    assert len(predictions) == manifest["students"]


def test_active_deployment_artifacts_execute():
    students = pd.read_parquet(path("data", "processed", "students_cleaned.parquet")).head(20).copy()
    unsup = joblib.load(path("models", "tracks", "unsupervised_pipeline.joblib"))
    X = unsup["preprocessor"].transform(students[unsup["features"]])
    assert len(unsup["model"].predict(X)) == 20
    supervised = joblib.load(path("models", "tracks", "supervised_certification_pipeline.joblib"))
    students["video_missing_any"] = students["video_missing_records"].gt(0).astype("int8")
    contract = load_json("models", "tracks", "input_contract.json")
    required = contract["supervised_learning"]["required_features"]
    probabilities = supervised.predict_proba(students[required])[:, 1]
    assert len(probabilities) == 20
    assert ((probabilities >= 0) & (probabilities <= 1)).all()


def test_dashboard_tracks_segments_and_sentence_embedding_removal():
    with open(path("reports", "student_segmentation_report.html"), encoding="utf-8") as handle:
        html = handle.read()
    for label in ["Project Overview", "Traditional Unsupervised", "Deep Learning", "Supervised Learning", "LLM", "Results Summary"]:
        assert label in html
    assert 'data-view="eda"' not in html
    assert 'id="eda"' not in html
    overview = html.split('<section class="view active" id="overview">', 1)[1].split('</section>', 1)[0]
    assert "EDA เชิงลึกและการเปรียบเทียบ" in overview
    for figure in [
        "full_distributions.png", "robust_boxplots.png", "zero_missing_outlier_profile.png",
        "behavior_relationships.png", "segment_feature_comparison.png",
        "segment_distribution_comparison.png", "segment_cluster_comparison.png",
        "segment_outcome_comparison.png",
        "activity_outlier_diagnostics.png", "video_quality_diagnostics.png",
            "k_sensitivity_multiseed_audit.csv", "persona_proportions.png",
        "deep_model_comparison.png", "deep_confusion_matrices.png", "deep_roc_calibration.png",
    ]:
        assert figure in html
    assert "Sentence Embedding</button>" not in html
    segments = load_json("outputs", "reproducibility", "dashboard_segment_summary.json")
    assert set(segments["segments"]) == {"all", "high_engagement", "low_engagement", "certified_only"}
    assert segments["segments"]["all"]["students"] == 446_766


def test_llm_student_rows_are_serialized_and_evaluated_without_target_leakage():
    manifest = load_json("outputs", "reproducibility", "analysis_tracks_manifest.json")
    llm = manifest["generative_llm"]
    text = pd.read_csv(path("outputs", "tables", "llm_student_text_inputs.csv"))
    models = pd.read_csv(path("outputs", "tables", "llm_text_classifier_comparison.csv"))
    confusions = pd.read_csv(path("outputs", "tables", "llm_text_confusion_matrices.csv"))
    assert llm["status"].startswith("Completed")
    assert llm["unit_of_analysis"] == "one row per student"
    assert len(text) == llm["sample_students"] == 12_000
    assert len(models) >= 3 and models["selected"].sum() == 1
    assert models["model_name"].str.contains("DistilBERT").any()
    assert len(confusions) == len(models)
    assert text["target_stored_separately"].eq(True).all()
    assert not text["student_behavior_text"].str.contains("certified", case=False).any()
    assert text["student_behavior_text"].str.contains("video plays", case=False).all()
    assert not text["student_behavior_text"].str.contains("minutes watched|watch duration", case=False).any()
    assert "never included" in llm["target_leakage_guard"]
    assert os.path.exists(path("outputs", "tables", "llm_task_definition.csv"))
    assert os.path.exists(path("models", "tracks", "llm_student_text_classifier.joblib"))


def test_dashboard_contains_uniform_interactive_charts():
    html = open(path("reports", "student_segmentation_report.html"), encoding="utf-8").read()
    assert html.count("interactive-chart-card") >= 6
    assert "plotly-graph-div" in html
    assert "scrollZoom" in html
    assert "llm_text_classifier_comparison.csv" in html
    assert "llm_text_confusion_matrices.csv" in html
    assert "One-Student-Row-to-Text LLM / Transformer" in html
    assert "llm_generative_model_comparison.csv" in html
    assert "gemini-3.5-flash-lite" in html


def test_hosted_generative_ai_has_empirical_predictions_and_privacy_guard():
    comparison = pd.read_csv(path("outputs", "tables", "llm_generative_model_comparison.csv"))
    predictions = pd.read_csv(path("outputs", "tables", "llm_api_predictions_all.csv"))
    providers = pd.read_csv(path("outputs", "tables", "llm_api_provider_status.csv"))
    gemini = comparison.loc[comparison["provider"].eq("Gemini")].iloc[0]
    assert gemini["evaluation_students"] == 1_800
    assert gemini["requests"] == 90
    assert gemini["total_tokens"] > 0
    assert len(predictions) == 1_800
    assert predictions["row_id"].nunique() == 1_800
    assert predictions["probability"].between(0, 1).all()
    assert {"Gemini", "OpenAI", "Anthropic", "Ollama"}.issubset(set(providers["provider"]))
    assert providers.loc[providers["provider"].eq("Gemini"), "status"].iloc[0] == "completed"
    assert providers.loc[providers["provider"].eq("OpenAI"), "reason"].iloc[0] == "paid_api_excluded_by_free_only_policy"
    assert providers.loc[providers["provider"].eq("Anthropic"), "reason"].iloc[0] == "paid_api_excluded_by_free_only_policy"


def test_segment_eda_comparison_artifacts():
    comparison = pd.read_csv(path("outputs", "tables", "segment_comparison.csv"))
    distributions = pd.read_csv(path("outputs", "tables", "segment_feature_distributions.csv"))
    assert set(comparison["segment"]) == {"all", "high_engagement", "low_engagement", "certified_only"}
    assert set(distributions["segment"]) == set(comparison["segment"])
    assert {"p05", "p25", "median", "p75", "p95"}.issubset(distributions.columns)
    for figure in [
        "segment_feature_comparison.png", "segment_outcome_comparison.png",
        "segment_cluster_comparison.png", "segment_distribution_comparison.png",
    ]:
        assert os.path.exists(path("outputs", "figures", "tracks", figure))


def test_k_selection_has_gap_and_auditable_votes():
    manifest = load_json("outputs", "reproducibility", "unsupervised_track_manifest.json")
    gap = pd.read_csv(path("outputs", "tables", "gap_statistic_by_k.csv"))
    decision = pd.read_csv(path("outputs", "tables", "k_selection_decision.csv"))
    assert {"k", "gap", "gap_se", "gap_rule_selected"}.issubset(gap.columns)
    assert len(decision) == 5
    assert not decision["criterion"].str.contains("elbow", case=False, na=False).any()
    assert manifest["elbow_used_for_selection"] is False
    assert manifest["selected_k"] in manifest["consensus_k_candidates"]
    assert "Gap statistic one-standard-error rule" in manifest["metric_votes"]


def test_deep_track_compares_at_least_five_models():
    deep = pd.read_csv(path("outputs", "tables", "deep_learning_model_comparison.csv"))
    assert len(deep) >= 5
    assert deep["selected"].sum() == 1


def test_monitoring_is_honest_about_missing_future_cohort():
    baseline = load_json("monitoring", "track_monitoring_baseline.json")
    decision = load_json("monitoring", "track_retraining_decision.json")
    assert baseline["future_cohorts_evaluated"] == 0
    assert decision["status"] == "NOT_EVALUATED"


def run_all_tests():
    tests = [
        test_unsupervised_features_are_selected_from_clean_merged_data,
        test_k_is_data_selected_and_all_students_are_assigned,
        test_supervised_feature_contract_and_test_metrics,
        test_deep_learning_is_classification_not_clustering,
        test_active_deployment_artifacts_execute,
        test_dashboard_tracks_segments_and_sentence_embedding_removal,
        test_llm_student_rows_are_serialized_and_evaluated_without_target_leakage,
        test_dashboard_contains_uniform_interactive_charts,
        test_hosted_generative_ai_has_empirical_predictions_and_privacy_guard,
        test_segment_eda_comparison_artifacts,
        test_k_selection_has_gap_and_auditable_votes,
        test_deep_track_compares_at_least_five_models,
        test_monitoring_is_honest_about_missing_future_cohort,
    ]
    for test in tests:
        test()
        print(f"[PASS] {test.__name__}")


if __name__ == "__main__":
    run_all_tests()

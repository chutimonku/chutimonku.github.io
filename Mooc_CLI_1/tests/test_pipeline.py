import json
import unittest

import pandas as pd

from src.pipeline import predict_certification, predict_clusters
from src.workflow import CLASS_FEATURES, CLUSTER_FEATURES, FINAL_MODELS, PROCESSED, REPRO, sha256_file

class WorkflowArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.classification = pd.read_parquet(PROCESSED / "classification_records.parquet").head(25)
        cls.students = pd.read_parquet(PROCESSED / "students_cleaned.parquet").head(25)

    def test_group_splits_have_no_overlap(self):
        full = pd.read_parquet(PROCESSED / "classification_records.parquet", columns=["userid_DI", "split"])
        sets = {name: set(full.loc[full.split == name, "userid_DI"]) for name in ["train", "validation", "test"]}
        self.assertFalse(sets["train"] & sets["validation"])
        self.assertFalse(sets["train"] & sets["test"])
        self.assertFalse(sets["validation"] & sets["test"])

    def test_classification_inference(self):
        result = predict_certification(self.classification[CLASS_FEATURES])
        self.assertEqual(len(result), len(self.classification))
        self.assertTrue(result.certification_score.between(0, 1).all())

    def test_classification_leakage_guard(self):
        bad = self.classification[CLASS_FEATURES].copy(); bad["grade"] = 1.0
        with self.assertRaises(ValueError):
            predict_certification(bad)

    def test_cluster_inference_and_leakage_guard(self):
        result = predict_clusters(self.students[CLUSTER_FEATURES])
        self.assertEqual(len(result), len(self.students))
        bad = self.students[CLUSTER_FEATURES].copy(); bad["certified"] = 1
        with self.assertRaises(ValueError):
            predict_clusters(bad)

    def test_model_hashes_match_locks(self):
        for branch in ["classification", "clustering"]:
            lock = json.loads((FINAL_MODELS / f"{branch}_model_lock.json").read_text())
            self.assertEqual(lock["sha256"], sha256_file(FINAL_MODELS / f"{branch}_pipeline.joblib"))

    def test_artifact_check_passed(self):
        check = json.loads((REPRO / "artifact_check.json").read_text())
        self.assertTrue(check["overall_pass"])
        self.assertTrue(check["raw_unchanged"])

if __name__ == "__main__":
    unittest.main()

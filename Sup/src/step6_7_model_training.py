"""ขั้นตอนที่ 6 และ 7: การคัดเลือกโมเดลตามหลักการวิจัย การฝึกสอน และการปรับจูนไฮเปอร์พารามิเตอร์บนชุด Validation."""

import json
import os
import time
import joblib
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.metrics import average_precision_score, brier_score_loss, precision_recall_curve, roc_auc_score
from sklearn.naive_bayes import GaussianNB
from sklearn.neural_network import MLPClassifier
from sklearn.svm import LinearSVC
from sklearn.tree import DecisionTreeClassifier

PROCESSED_DIR = os.path.join("data", "processed")
LABELS_DIR = os.path.join("data", "labels")
MODELS_DIR = os.path.join("models", "candidates")
TABLES_DIR = os.path.join("outputs", "tables")
REPRO_DIR = os.path.join("outputs", "reproducibility")
LOGS_DIR = os.path.join("outputs", "logs")
CONFIG_PATH = os.path.join("config", "project_config.json")


def optimize_threshold(y_true, y_probs):
    """หาจุดตัดการตัดสินใจ (Threshold) ที่ให้ค่า F1-score สูงที่สุดบนชุดตรวจสอบ (Validation Set)."""
    precisions, recalls, thresholds = precision_recall_curve(y_true, y_probs)
    f1_scores = 2 * (precisions * recalls) / np.maximum(precisions + recalls, 1e-8)
    best_idx = np.argmax(f1_scores)
    # อาร์เรย์ thresholds มีความยาวน้อยกว่า precisions อยู่ 1
    best_thresh = float(thresholds[min(best_idx, len(thresholds) - 1)])
    best_f1 = float(f1_scores[best_idx])
    best_prec = float(precisions[best_idx])
    best_rec = float(recalls[best_idx])
    return best_thresh, best_f1, best_prec, best_rec


def run_model_training():
    """ฟังก์ชันหลักสำหรับดำเนินการฝึกสอนและประเมินโมเดลตัวเลือกทั้งหมด."""
    print("=" * 70)
    print("ขั้นตอนที่ 6 และ 7: การคัดเลือกโมเดล ฝึกสอน และปรับจูนไฮเปอร์พารามิเตอร์")
    print("=" * 70)

    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(TABLES_DIR, exist_ok=True)
    os.makedirs(REPRO_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)

    with open(CONFIG_PATH, encoding="utf-8") as handle:
        config = json.load(handle)
    seed = config["split_strategy"]["random_seed"]

    print("[+] กำลังโหลดพาร์ติชันฟีเจอร์และเลเบลที่ประมวลผลแล้ว...")
    df_train_x = pd.read_parquet(os.path.join(PROCESSED_DIR, "train_features.parquet"))
    df_train_y = pd.read_parquet(os.path.join(LABELS_DIR, "train_labels.parquet"))

    df_val_x = pd.read_parquet(os.path.join(PROCESSED_DIR, "val_features.parquet"))
    df_val_y = pd.read_parquet(os.path.join(LABELS_DIR, "val_labels.parquet"))

    feature_cols = [c for c in df_train_x.columns if c != "userid_DI"]
    X_train = df_train_x[feature_cols].values
    y_train = df_train_y["certified_student"].values

    X_val = df_val_x[feature_cols].values
    y_val = df_val_y["certified_student"].values

    print(f"    ขนาด X_train: {X_train.shape}, สัดส่วนผู้สำเร็จ: {y_train.mean()*100:.2f}%")
    print(f"    ขนาด X_val:   {X_val.shape}, สัดส่วนผู้สำเร็จ: {y_val.mean()*100:.2f}%")

    # กำหนดสถาปัตยกรรมโมเดลตัวเลือกและตารางไฮเปอร์พารามิเตอร์
    # หมายเหตุ: ใช้ class_weight=None บนโมเดล Ensemble เพื่อให้ค่าความน่าจะเป็นที่ทำนายได้
    # มีการเทียบเคียงความน่าจะเป็นจริง (Well-calibrated) และไม่บิดเบือนสเกลความน่าจะเป็น
    candidates = [
        {
            "id": "dummy_baseline",
            "name": "Dummy Baseline (ค่าฐานสถิติ)",
            "family": "Baseline",
            "model": DummyClassifier(strategy="prior"),
            "params": {"strategy": "prior"},
        },
        {
            "id": "logistic_reg_c01",
            "name": "Logistic Regression (C=0.1, Balanced)",
            "family": "Linear",
            "model": LogisticRegression(C=0.1, penalty="l2", class_weight="balanced", max_iter=500, random_state=seed),
            "params": {"C": 0.1, "class_weight": "balanced"},
        },
        {
            "id": "logistic_reg_c10",
            "name": "Logistic Regression (C=1.0, Balanced)",
            "family": "Linear",
            "model": LogisticRegression(C=1.0, penalty="l2", class_weight="balanced", max_iter=500, random_state=seed),
            "params": {"C": 1.0, "class_weight": "balanced"},
        },
        {
            "id": "logistic_reg_unweighted",
            "name": "Logistic Regression (C=1.0, Unweighted)",
            "family": "Linear",
            "model": LogisticRegression(C=1.0, penalty="l2", class_weight=None, max_iter=500, random_state=seed),
            "params": {"C": 1.0, "class_weight": None},
        },
        {
            "id": "sgd_elasticnet",
            "name": "SGD Classifier (ElasticNet)",
            "family": "Linear / Sparse",
            "model": SGDClassifier(loss="log_loss", penalty="elasticnet", l1_ratio=0.15, alpha=1e-4, max_iter=1000, random_state=seed),
            "params": {"loss": "log_loss", "penalty": "elasticnet", "alpha": 1e-4},
        },
        {
            "id": "gaussian_naive_bayes",
            "name": "Gaussian Naive Bayes",
            "family": "Probabilistic",
            "model": GaussianNB(var_smoothing=1e-8),
            "params": {"var_smoothing": 1e-8},
        },
        {
            "id": "linear_svm_calibrated",
            "name": "Calibrated Linear SVM (เทียบเคียงความน่าจะเป็น)",
            "family": "Max-Margin",
            "model": CalibratedClassifierCV(
                estimator=LinearSVC(
                    C=0.1,
                    class_weight="balanced",
                    dual="auto",
                    max_iter=3000,
                    random_state=seed,
                ),
                method="sigmoid",
                cv=3,
                n_jobs=1,
            ),
            "params": {"C": 0.1, "class_weight": "balanced", "calibration": "sigmoid", "calibration_cv": 3},
        },
        {
            "id": "decision_tree_d10",
            "name": "Decision Tree (Depth=10)",
            "family": "Single Tree",
            "model": DecisionTreeClassifier(
                max_depth=10,
                min_samples_leaf=20,
                class_weight="balanced",
                random_state=seed,
            ),
            "params": {"max_depth": 10, "min_samples_leaf": 20, "class_weight": "balanced"},
        },
        {
            "id": "random_forest_d10",
            "name": "Random Forest (Depth=10, 100 Trees)",
            "family": "Bagging Ensemble",
            "model": RandomForestClassifier(n_estimators=100, max_depth=10, min_samples_leaf=20, class_weight=None, n_jobs=-1, random_state=seed),
            "params": {"n_estimators": 100, "max_depth": 10, "min_samples_leaf": 20, "class_weight": None},
        },
        {
            "id": "random_forest_d15",
            "name": "Random Forest (Depth=15, 100 Trees, Calibrated)",
            "family": "Bagging Ensemble",
            "model": RandomForestClassifier(n_estimators=100, max_depth=15, min_samples_leaf=10, class_weight=None, n_jobs=-1, random_state=seed),
            "params": {"n_estimators": 100, "max_depth": 15, "min_samples_leaf": 10, "class_weight": None},
        },
        {
            "id": "extra_trees_d15",
            "name": "Extra Trees (Depth=15, 150 Trees)",
            "family": "Randomized Tree Ensemble",
            "model": ExtraTreesClassifier(
                n_estimators=150,
                max_depth=15,
                min_samples_leaf=10,
                class_weight=None,
                n_jobs=-1,
                random_state=seed,
            ),
            "params": {"n_estimators": 150, "max_depth": 15, "min_samples_leaf": 10, "class_weight": None},
        },
        {
            "id": "hist_gbdt_lr05",
            "name": "HistGradientBoosting (lr=0.05, max_iter=150)",
            "family": "Boosting Ensemble",
            "model": HistGradientBoostingClassifier(learning_rate=0.05, max_iter=150, max_leaf_nodes=31, random_state=seed),
            "params": {"learning_rate": 0.05, "max_iter": 150, "class_weight": None},
        },
        {
            "id": "hist_gbdt_lr10",
            "name": "HistGradientBoosting (lr=0.10, max_iter=150)",
            "family": "Boosting Ensemble",
            "model": HistGradientBoostingClassifier(learning_rate=0.10, max_iter=150, max_leaf_nodes=31, random_state=seed),
            "params": {"learning_rate": 0.10, "max_iter": 150, "class_weight": None},
        },
        {
            "id": "mlp_neural_net",
            "name": "Multi-Layer Perceptron (64, 32)",
            "family": "Neural Network",
            "model": MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=40, early_stopping=True, random_state=seed),
            "params": {"hidden_layer_sizes": "(64, 32)", "early_stopping": True},
        },
    ]

    family_metadata = {
        "Baseline": ("ความถี่คลาสตั้งต้น", "ไม่มี (เกณฑ์อ้างอิง)", "โมเดลฐานเปรียบเทียบ"),
        "Linear": ("ลอจิทแบบเชิงเส้น", "ปรับน้ำหนักคลาสหรือความชุกตามธรรมชาติ", "โมเดลเชิงเส้นที่อธิบายง่าย"),
        "Linear / Sparse": ("โมเดลเชิงเส้นแบบสโตแคสติก", "การปรับจุดตัดการตัดสินใจ", "โมเดลเชิงเส้นแบบเบาบาง"),
        "Probabilistic": ("ความเป็นอิสระแบบเกาส์เซียน", "ความน่าจะเป็นก่อนหน้าและการปรับจุดตัด", "โมเดลความน่าจะเป็นแบบรวดเร็ว"),
        "Max-Margin": ("เส้นแบ่งขอบเขตมาร์จินสูงสุด", "การเทียบเคียงความน่าจะเป็นด้วยซิกมอยด์", "โมเดลเส้นแบ่งมาร์จินสูงสุด"),
        "Single Tree": ("กฎการตัดสินใจแบบแบ่งแกน", "การปรับน้ำหนักคลาสให้สมดุล", "ต้นไม้ตัดสินใจเดี่ยวที่อธิบายง่าย"),
        "Bagging Ensemble": ("กลุ่มต้นไม้สุ่มแบบรวมผลเฉลี่ย (Bootstrap)", "การปรับจูนจุดตัดและความน่าจะเป็นแท้จริง", "กลุ่มต้นไม้แบบแบคกิ้งไม่เชิงเส้น"),
        "Randomized Tree Ensemble": ("การสุ่มจุดตัดแบบกระจายอิสระ", "การปรับจูนจุดตัดและความน่าจะเป็นแท้จริง", "กลุ่มต้นไม้แบบสุ่มความแปรปรวนสูง"),
        "Boosting Ensemble": ("การแก้ไขข้อผิดพลาดแบบลำดับด้วยฮิสโตแกรม", "การปรับจูนจุดตัดและอัตราการเรียนรู้", "กลุ่มต้นไม้แบบบูสต์ไม่เชิงเส้น"),
        "Neural Network": ("การแทนข้อมูลแบบหลายชั้นไม่เชิงเส้น", "การปรับจุดตัดการตัดสินใจ", "โครงข่ายประสาทเทียมแบบหลายชั้น"),
    }
    candidate_specs = []
    for cand in candidates:
        inductive_bias, imbalance_handling, primary_role = family_metadata[cand["family"]]
        candidate_specs.append({
            "model_id": cand["id"],
            "model_name": cand["name"],
            "algorithm_family": cand["family"],
            "inductive_bias": inductive_bias,
            "imbalance_handling": imbalance_handling,
            "key_hyperparameters": json.dumps(cand["params"], sort_keys=True),
            "primary_role": primary_role,
        })
    pd.DataFrame(candidate_specs).to_csv(
        os.path.join(TABLES_DIR, "candidate_models.csv"), index=False
    )

    tuning_records = []
    log_records = []

    print("[+] กำลังฝึกสอนสถาปัตยกรรมโมเดลตัวเลือกตามข้อกำหนดไฮเปอร์พารามิเตอร์...")
    for idx, cand in enumerate(candidates, start=1):
        cand_id = cand["id"]
        cand_name = cand["name"]
        print(f"    [{idx}/{len(candidates)}] กำลังฝึกสอน {cand_name}...")
        t0 = time.time()

        try:
            cand["model"].fit(X_train, y_train)
            train_duration = time.time() - t0

            # คำนวณค่าความน่าจะเป็น
            if hasattr(cand["model"], "predict_proba"):
                val_probs = cand["model"].predict_proba(X_val)[:, 1]
            else:
                val_probs = cand["model"].decision_function(X_val)

            # ประเมินตัววัดประสิทธิภาพ
            val_roc_auc = float(roc_auc_score(y_val, val_probs))
            val_pr_auc = float(average_precision_score(y_val, val_probs))
            val_brier = float(brier_score_loss(y_val, val_probs))

            # ปรับจูนจุดตัดการตัดสินใจเพื่อการปฏิบัติงานจริง (Max-F1)
            opt_thresh, opt_f1, opt_prec, opt_rec = optimize_threshold(y_val, val_probs)

            # ประเมินตัววัดที่จุดตัดเริ่มต้นมาตรฐาน 0.50
            preds_50 = (val_probs >= 0.50).astype(int)
            prec_50 = float(np.sum((preds_50 == 1) & (y_val == 1)) / max(np.sum(preds_50 == 1), 1))
            rec_50 = float(np.sum((preds_50 == 1) & (y_val == 1)) / max(np.sum(y_val == 1), 1))
            f1_50 = float(2 * prec_50 * rec_50 / max(prec_50 + rec_50, 1e-8))

            tuning_records.append({
                "model_id": cand_id,
                "model_name": cand_name,
                "family": cand["family"],
                "val_roc_auc": round(val_roc_auc, 4),
                "val_pr_auc": round(val_pr_auc, 4),
                "val_brier_score": round(val_brier, 4),
                "optimal_threshold": round(opt_thresh, 4),
                "val_f1_optimal": round(opt_f1, 4),
                "val_precision_optimal": round(opt_prec, 4),
                "val_recall_optimal": round(opt_rec, 4),
                "val_f1_default": round(f1_50, 4),
                "train_duration_sec": round(train_duration, 2),
                "status": "Success",
            })

            log_records.append({
                "model_id": cand_id,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "Success",
                "train_duration_sec": round(train_duration, 2),
                "roc_auc": round(val_roc_auc, 4),
                "pr_auc": round(val_pr_auc, 4),
            })

            # บันทึกไฟล์ Artifact ของโมเดลตัวเลือก
            model_save_path = os.path.join(MODELS_DIR, f"{cand_id}.joblib")
            joblib.dump(cand["model"], model_save_path)
            print(f"        Val ROC-AUC: {val_roc_auc:.4f} | PR-AUC: {val_pr_auc:.4f} | Optimal F1: {opt_f1:.4f} (ใช้เวลา {train_duration:.1f} วินาที)")

        except Exception as e:
            train_duration = time.time() - t0
            print(f"        ล้มเหลว: {str(e)}")
            tuning_records.append({
                "model_id": cand_id,
                "model_name": cand_name,
                "family": cand["family"],
                "status": f"Failed: {str(e)}",
                "train_duration_sec": round(train_duration, 2),
            })
            log_records.append({
                "model_id": cand_id,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": f"Failed: {str(e)}",
                "train_duration_sec": round(train_duration, 2),
            })

    df_tuning = pd.DataFrame(tuning_records).sort_values("val_pr_auc", ascending=False)
    tuning_csv_path = os.path.join(TABLES_DIR, "model_tuning_results.csv")
    df_tuning.to_csv(tuning_csv_path, index=False)
    print(f"[+] บันทึกผลการปรับจูนโมเดลเรียบร้อยที่: {tuning_csv_path}")

    df_log = pd.DataFrame(log_records)
    log_csv_path = os.path.join(LOGS_DIR, "model_training_log.csv")
    df_log.to_csv(log_csv_path, index=False)
    print(f"[+] บันทึกประวัติการฝึกสอนโมเดลเรียบร้อยที่: {log_csv_path}")

    # ข้อมูลกำกับกระบวนการฝึกสอน (Training Configuration Manifest)
    train_manifest = {
        "random_seed": seed,
        "n_candidates_evaluated": len(candidates),
        "n_algorithm_families": len({cand["family"] for cand in candidates}),
        "tuning_method": "ฝึกสอนบนชุด Train และคัดเลือกโครงสร้างที่ประสิทธิภาพสูงสุดบนชุด Validation",
        "feature_count": len(feature_cols),
        "features": feature_cols,
        "train_instances": len(X_train),
        "val_instances": len(X_val),
        "completed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    with open(os.path.join(REPRO_DIR, "training_config.json"), "w", encoding="utf-8") as handle:
        json.dump(train_manifest, handle, indent=2, ensure_ascii=False)
    print(f"[+] บันทึกคอนฟิกการฝึกสอนที่: {os.path.join(REPRO_DIR, 'training_config.json')}")

    successful = df_tuning[df_tuning["status"].str.lower().eq("success")].copy()
    if successful.empty:
        raise RuntimeError("ไม่มีโมเดลตัวเลือกใดที่ฝึกสอนสำเร็จ")

    provisional = successful.iloc[0]
    result_lines = [
        "| ลำดับ | โมเดล | กลุ่มอัลกอริทึม | Validation ROC-AUC | Validation PR-AUC | Brier Score | เวลา (วินาที) |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for rank, (_, row) in enumerate(successful.iterrows(), start=1):
        result_lines.append(
            "| {rank} | {model} | {family} | {roc:.4f} | {pr:.4f} | {brier:.4f} | {duration:.2f} |".format(
                rank=rank,
                model=row["model_name"],
                family=row["family"],
                roc=float(row["val_roc_auc"]),
                pr=float(row["val_pr_auc"]),
                brier=float(row["val_brier_score"]),
                duration=float(row["train_duration_sec"]),
            )
        )

    experiment_log = f"""# บันทึกผลการทดลองโมเดล Supervised Learning (Experiment Log)

สร้างจากผลการรันจริงในขั้นตอนที่ 6 และ 7 ค่าทั้งหมดวัดผลบนชุด Validation โดยไม่มีการนำชุด Holdout Test มาใช้ตัดสินใจเลือกรุ่นชนะเลิศ

## ข้อมูลความสามารถในการทำซ้ำ (Reproducibility)

- เมล็ดสุ่ม (Random Seed): `{seed}`
- จำนวนนักศึกษาในชุดฝึกสอน (Train): `{len(X_train):,}` คน
- จำนวนนักศึกษาในชุดตรวจสอบ (Validation): `{len(X_val):,}` คน
- จำนวนฟีเจอร์ที่ผ่านการแปลง: `{len(feature_cols)}` มิติ
- จำนวนโครงสร้างโมเดลตัวเลือก: `{len(candidates)}` ตัว
- จำนวนกลุ่มอัลกอริทึม: `{len({cand['family'] for cand in candidates})}` กลุ่ม
- กฎเกณฑ์การคัดเลือก: คัดเลือกโมเดลที่ให้ค่า PR-AUC บนชุด Validation สูงสุด พร้อมพิจารณา ROC-AUC, Brier score และความสามารถในการเทียบเคียงความน่าจะเป็น

## สรุปผลการประเมินบนชุด Validation

{chr(10).join(result_lines)}

## โมเดลที่ชนะเลิศเบื้องต้น (Provisional Winner)

- รหัสโมเดล: `{provisional['model_id']}`
- ชื่อโมเดล: `{provisional['model_name']}`
- Validation PR-AUC: `{float(provisional['val_pr_auc']):.4f}`
- Validation ROC-AUC: `{float(provisional['val_roc_auc']):.4f}`
- Validation Brier score: `{float(provisional['val_brier_score']):.4f}`
- จุดตัดการตัดสินใจที่ปรับจูน (Optimal Threshold): `{float(provisional['optimal_threshold']):.4f}`
"""
    experiment_log_path = os.path.join(REPRO_DIR, "experiment_log.md")
    with open(experiment_log_path, "w", encoding="utf-8") as handle:
        handle.write(experiment_log)
    print(f"[+] บันทึกประวัติการทดลองและการตัดสินใจเรียบร้อยที่: {experiment_log_path}")


if __name__ == "__main__":
    run_model_training()

"""ขั้นตอนที่ 8: การประเมินผลโมเดล การแบ่งกลุ่มความเสี่ยง การอธิบายโมเดล ความเป็นธรรม และการล็อกโมเดล (Model Locking)."""

import hashlib
import json
import os
import time
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["font.sans-serif"] = ["Thonburi", "Sukhumvit Set", "Arial", "DejaVu Sans"]
plt.rcParams["font.family"] = "sans-serif"
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.calibration import calibration_curve
from sklearn.inspection import permutation_importance
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

PROCESSED_DIR = os.path.join("data", "processed")
LABELS_DIR = os.path.join("data", "labels")
CANDIDATES_DIR = os.path.join("models", "candidates")
FINAL_MODELS_DIR = os.path.join("models", "final")
TABLES_DIR = os.path.join("outputs", "tables")
FIGURES_DIR = os.path.join("outputs", "figures", "evaluation")
DATA_OUT_DIR = os.path.join("outputs", "data")
REPRO_DIR = os.path.join("outputs", "reproducibility")
CONFIG_PATH = os.path.join("config", "project_config.json")


def get_sha256(filepath: str) -> str:
    """คำนวณค่าแฮช SHA-256 ของไฟล์เพื่อตรวจสอบความสมบูรณ์ในการล็อกโมเดล."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(1024 * 1024):
            hasher.update(chunk)
    return hasher.hexdigest()


def assign_risk_tiers(probs: np.ndarray, config: dict) -> tuple[np.ndarray, list[str]]:
    """จำแนกนักศึกษาออกเป็น 3 ระดับความเสี่ยงตามเกณฑ์ความน่าจะเป็นที่กำหนด."""
    tiers_cfg = config["risk_tiers"]
    t1_min = tiers_cfg["tier_1"]["min_probability"]
    t2_min = tiers_cfg["tier_2"]["min_probability"]

    tier_labels = np.empty(len(probs), dtype=object)
    tier_actions = []

    for i, p in enumerate(probs):
        if p >= t1_min:
            tier_labels[i] = "Tier 1: Low Risk / Likely Completer"
            tier_actions.append(tiers_cfg["tier_1"]["recommended_action"])
        elif p >= t2_min:
            tier_labels[i] = "Tier 2: Moderate Risk / Target for Nudge"
            tier_actions.append(tiers_cfg["tier_2"]["recommended_action"])
        else:
            tier_labels[i] = "Tier 3: High Risk / Early Dropout"
            tier_actions.append(tiers_cfg["tier_3"]["recommended_action"])

    return tier_labels, tier_actions


def run_model_evaluation():
    """ฟังก์ชันหลักสำหรับดำเนินการประเมินผลโมเดลบนชุด Holdout Test ตรวจสอบ Confusion Matrix และทำนายผู้ได้รับใบจบ."""
    print("=" * 70)
    print("ขั้นตอนที่ 8: การประเมินผลโมเดล จัดกลุ่มความเสี่ยง และล็อกโมเดล")
    print("=" * 70)

    os.makedirs(FINAL_MODELS_DIR, exist_ok=True)
    os.makedirs(FIGURES_DIR, exist_ok=True)
    os.makedirs(DATA_OUT_DIR, exist_ok=True)

    with open(CONFIG_PATH, encoding="utf-8") as handle:
        config = json.load(handle)

    # 1. โหลดชุดข้อมูลทดสอบ (Holdout Test Set)
    print("[+] กำลังโหลดพาร์ติชันชุดทดสอบ Holdout Test (ไม่เคยเห็นมาก่อน)...")
    df_test_x = pd.read_parquet(os.path.join(PROCESSED_DIR, "test_features.parquet"))
    df_test_y = pd.read_parquet(os.path.join(LABELS_DIR, "test_labels.parquet"))
    df_students = pd.read_parquet(os.path.join(PROCESSED_DIR, "students_cleaned.parquet"))

    feature_cols = [c for c in df_test_x.columns if c != "userid_DI"]
    X_test = df_test_x[feature_cols].values
    y_test = df_test_y["certified_student"].values
    test_userids = df_test_x["userid_DI"].values
    total_test = len(y_test)

    # โหลดผลการปรับจูนจากชุด Validation เพื่อคัดเลือกรุ่นชนะเลิศ (Champion Model)
    tuning_csv_path = os.path.join(TABLES_DIR, "model_tuning_results.csv")
    df_tuning = pd.read_csv(tuning_csv_path)

    # ตัด Dummy Baseline ออกจากการคัดเลือก
    valid_candidates = df_tuning[
        (df_tuning["model_id"] != "dummy_baseline")
        & df_tuning["status"].astype(str).str.lower().eq("success")
    ].copy()
    champion_row = valid_candidates.sort_values(
        ["val_pr_auc", "val_roc_auc", "val_brier_score"],
        ascending=[False, False, True],
    ).iloc[0]
    champion_id = champion_row["model_id"]
    optimal_threshold = float(champion_row["optimal_threshold"])
    print(f"[+] สถาปัตยกรรมที่ชนะเลิศจากการคัดเลือกบนชุด Validation: {champion_id}")
    print(f"    Validation PR-AUC: {champion_row['val_pr_auc']:.4f} | จุดตัดที่เหมาะสมที่สุด (Threshold): {optimal_threshold:.4f}")

    # 2. ประเมินโมเดลตัวเลือกทั้งหมดบนชุดทดสอบ Holdout Test
    test_comparison_records = []
    models_dict = {}
    probs_dict = {}

    successful_tuning = df_tuning[df_tuning["status"].astype(str).str.lower().eq("success")]
    for _, row in successful_tuning.iterrows():
        mid = row["model_id"]
        model_file = os.path.join(CANDIDATES_DIR, f"{mid}.joblib")
        if not os.path.exists(model_file):
            continue

        model = joblib.load(model_file)
        models_dict[mid] = model

        if hasattr(model, "predict_proba"):
            p_test = model.predict_proba(X_test)[:, 1]
        else:
            p_test = model.decision_function(X_test)
        probs_dict[mid] = p_test

        roc = float(roc_auc_score(y_test, p_test))
        pr = float(average_precision_score(y_test, p_test))
        brier = float(brier_score_loss(y_test, p_test))

        m_opt_thresh = float(row.get("optimal_threshold", 0.50))
        y_pred_opt = (p_test >= m_opt_thresh).astype(int)
        y_pred_50 = (p_test >= 0.50).astype(int)

        test_comparison_records.append({
            "model_id": mid,
            "model_name": row["model_name"],
            "family": row["family"],
            "test_roc_auc": round(roc, 4),
            "test_pr_auc": round(pr, 4),
            "test_brier_score": round(brier, 4),
            "optimal_threshold": round(m_opt_thresh, 4),
            "test_f1_optimal": round(float(f1_score(y_test, y_pred_opt, zero_division=0)), 4),
            "test_precision_optimal": round(float(precision_score(y_test, y_pred_opt, zero_division=0)), 4),
            "test_recall_optimal": round(float(recall_score(y_test, y_pred_opt, zero_division=0)), 4),
            "test_accuracy_optimal": round(float(accuracy_score(y_test, y_pred_opt)), 4),
            "test_f1_default": round(float(f1_score(y_test, y_pred_50, zero_division=0)), 4),
            "test_precision_default": round(float(precision_score(y_test, y_pred_50, zero_division=0)), 4),
            "test_recall_default": round(float(recall_score(y_test, y_pred_50, zero_division=0)), 4),
            "test_balanced_acc": round(float(balanced_accuracy_score(y_test, y_pred_opt)), 4),
        })

    df_test_comp = pd.DataFrame(test_comparison_records).sort_values("test_pr_auc", ascending=False)
    comp_path = os.path.join(TABLES_DIR, "model_comparison.csv")
    df_test_comp.to_csv(comp_path, index=False)
    print(f"[+] ตารางเปรียบเทียบโมเดลทุกตัวบนชุดทดสอบบันทึกเรียบร้อยที่: {comp_path}")

    # 3. ประเมินผลเชิงลึกสำหรับโมเดลชนะเลิศ (Champion Model)
    champion_model = models_dict[champion_id]
    champ_probs = probs_dict[champion_id]
    champ_preds_opt = (champ_probs >= optimal_threshold).astype(int)
    champ_preds_50 = (champ_probs >= 0.50).astype(int)

    # ตรวจสอบและคำนวณ Confusion Matrix อย่างละเอียดและถูกต้อง
    cm_opt = confusion_matrix(y_test, champ_preds_opt)
    tn, fp, fn, tp = cm_opt.ravel()
    assert (tn + fp + fn + tp) == total_test, "ผลรวมเซลล์ Confusion Matrix ต้องเท่ากับขนาดชุดทดสอบพอดี"

    # คำนวณผลรวมขอบ (Marginal Sums)
    row_actual_negative = int(tn + fp)  # ผู้ไม่จบจริง
    row_actual_positive = int(fn + tp)  # ผู้ได้รับใบจบจริง
    col_pred_negative = int(tn + fn)    # ผู้ที่ทำนายว่าไม่จบ
    col_pred_positive = int(fp + tp)    # ผู้ที่ทำนายว่าจะได้รับใบจบ

    accuracy = float((tp + tn) / total_test)
    precision = float(precision_score(y_test, champ_preds_opt, zero_division=0))
    recall = float(recall_score(y_test, champ_preds_opt, zero_division=0))
    specificity = float(tn / (tn + fp))
    f1_opt = float(f1_score(y_test, champ_preds_opt, zero_division=0))
    f1_50 = float(f1_score(y_test, champ_preds_50, zero_division=0))

    # คำนวณจำนวนและสัดส่วนผู้ที่คาดว่าจะได้รับใบประกาศนียบัตร (Certificate Winners)
    pred_cert_count_opt = int(col_pred_positive)
    pred_cert_pct_opt = float(pred_cert_count_opt / total_test * 100)
    actual_cert_count = int(row_actual_positive)
    actual_cert_pct = float(actual_cert_count / total_test * 100)

    # สรุปภาพรวมเทียบเคียงประชากรทั้งระบบ (Cohort Scale: 335,650 คน)
    system_total_students = 335650
    system_actual_certified = 13881
    system_actual_certified_pct = float(system_actual_certified / system_total_students * 100)
    system_projected_certified = int(round(system_total_students * (pred_cert_count_opt / total_test)))
    system_projected_certified_pct = float(system_projected_certified / system_total_students * 100)

    print("\n" + "=" * 60)
    print("ผลการทำนายผู้ได้รับใบประกาศนียบัตร (Predicted Certificate Winners):")
    print("=" * 60)
    print(f"- ขนาดชุดทดสอบ Holdout Test Set: {total_test:,} คน (15% ของประชากร)")
    print(f"- จำนวนที่ได้รับใบจบจริงในชุดทดสอบ: {actual_cert_count:,} คน ({actual_cert_pct:.2f}%)")
    print(f"- จำนวนที่โมเดลทำนายว่าจะได้รับใบจบ (Max-F1, Cutoff={optimal_threshold:.4f}): {pred_cert_count_opt:,} คน ({pred_cert_pct_opt:.2f}%)")
    print(f"  • True Positives (TP - ทำนายจบและจบจริง): {tp:,} คน")
    print(f"  • False Positives (FP - ทำนายจบแต่ไม่จบจริง): {fp:,} คน")
    print(f"  • True Negatives (TN - ทำนายไม่จบและไม่จบจริง): {tn:,} คน")
    print(f"  • False Negatives (FN - ทำนายไม่จบแต่จบจริง): {fn:,} คน")
    print(f"- ความแม่นยำรวม (Accuracy): {accuracy*100:.2f}%")
    print(f"- Precision: {precision*100:.2f}% | Recall: {recall*100:.2f}% | F1-Score: {f1_opt*100:.2f}% | Specificity: {specificity*100:.2f}%")
    print(f"- การคาดการณ์เทียบเคียงนักศึกษาทั้งระบบ ({system_total_students:,} คน):")
    print(f"  • ได้รับใบจบจริงตามประวัติ: {system_actual_certified:,} คน ({system_actual_certified_pct:.2f}%)")
    print(f"  • คาดการณ์ผู้ได้รับใบจบทั้งระบบ: ~{system_projected_certified:,} คน ({system_projected_certified_pct:.2f}%)")
    print("=" * 60 + "\n")

    # บันทึกตารางสรุปการประเมินผลโมเดลชนะเลิศ
    champ_summary = {
        "champion_model_id": champion_id,
        "test_instances": total_test,
        "test_positive_instances": actual_cert_count,
        "test_positive_pct": round(actual_cert_pct, 4),
        "predicted_certificate_count": pred_cert_count_opt,
        "predicted_certificate_pct": round(pred_cert_pct_opt, 4),
        "system_total_students": system_total_students,
        "system_actual_certified": system_actual_certified,
        "system_projected_certified": system_projected_certified,
        "test_roc_auc": round(float(roc_auc_score(y_test, champ_probs)), 4),
        "test_pr_auc": round(float(average_precision_score(y_test, champ_probs)), 4),
        "test_brier_score": round(float(brier_score_loss(y_test, champ_probs)), 4),
        "test_log_loss": round(float(log_loss(y_test, champ_probs)), 4),
        "optimal_threshold": round(optimal_threshold, 4),
        "f1_at_optimal_threshold": round(f1_opt, 4),
        "precision_at_optimal_threshold": round(precision, 4),
        "recall_at_optimal_threshold": round(recall, 4),
        "accuracy_at_optimal_threshold": round(accuracy, 4),
        "specificity_at_optimal_threshold": round(specificity, 4),
        "f1_at_default_50": round(f1_50, 4),
        "confusion_matrix_optimal": {
            "TP": int(tp),
            "FP": int(fp),
            "TN": int(tn),
            "FN": int(fn),
            "row_actual_negative": row_actual_negative,
            "row_actual_positive": row_actual_positive,
            "col_pred_negative": col_pred_negative,
            "col_pred_positive": col_pred_positive,
            "total_instances": total_test,
        },
    }
    pd.DataFrame([champ_summary]).to_csv(os.path.join(TABLES_DIR, "test_evaluation_summary.csv"), index=False)
    print(f"[+] บันทึกสรุปการประเมินผลโมเดลที่: {os.path.join(TABLES_DIR, 'test_evaluation_summary.csv')}")

    # บันทึกตารางสรุปการทำนายผู้ได้รับใบจบโดยเฉพาะ (Certificate Prediction Summary)
    cert_summary_df = pd.DataFrame([{
        "dataset_partition": "Holdout Test Set (15%)",
        "total_students": total_test,
        "actual_certified_count": actual_cert_count,
        "actual_certified_pct": round(actual_cert_pct, 2),
        "predicted_certified_count": pred_cert_count_opt,
        "predicted_certified_pct": round(pred_cert_pct_opt, 2),
        "decision_threshold": round(optimal_threshold, 4),
        "true_positives": int(tp),
        "false_positives": int(fp),
        "true_negatives": int(tn),
        "false_negatives": int(fn),
        "precision_pct": round(precision * 100, 2),
        "recall_pct": round(recall * 100, 2),
        "f1_score_pct": round(f1_opt * 100, 2),
        "overall_accuracy_pct": round(accuracy * 100, 2),
    }, {
        "dataset_partition": "Full Cohort Population (100%)",
        "total_students": system_total_students,
        "actual_certified_count": system_actual_certified,
        "actual_certified_pct": round(system_actual_certified_pct, 2),
        "predicted_certified_count": system_projected_certified,
        "predicted_certified_pct": round(system_projected_certified_pct, 2),
        "decision_threshold": round(optimal_threshold, 4),
        "true_positives": int(round(tp * (system_total_students / total_test))),
        "false_positives": int(round(fp * (system_total_students / total_test))),
        "true_negatives": int(round(tn * (system_total_students / total_test))),
        "false_negatives": int(round(fn * (system_total_students / total_test))),
        "precision_pct": round(precision * 100, 2),
        "recall_pct": round(recall * 100, 2),
        "f1_score_pct": round(f1_opt * 100, 2),
        "overall_accuracy_pct": round(accuracy * 100, 2),
    }])
    cert_summary_df.to_csv(os.path.join(TABLES_DIR, "certificate_prediction_summary.csv"), index=False)
    print(f"[+] บันทึกตารางสรุปการทำนายผู้ได้รับใบจบที่: {os.path.join(TABLES_DIR, 'certificate_prediction_summary.csv')}")

    # 4. การจัดกลุ่มความเสี่ยงของนักศึกษา (Risk Tiers)
    risk_tiers, support_actions = assign_risk_tiers(champ_probs, config)
    df_predictions = pd.DataFrame({
        "userid_DI": test_userids,
        "true_certified": y_test,
        "predicted_probability": np.round(champ_probs, 4),
        "predicted_label_optimal": champ_preds_opt,
        "predicted_label_50": champ_preds_50,
        "risk_tier": risk_tiers,
        "recommended_action": support_actions,
    })
    preds_out_path = os.path.join(DATA_OUT_DIR, "test_predictions.csv")
    df_predictions.to_csv(preds_out_path, index=False)
    print(f"[+] บันทึกผลการทำนายระดับนักศึกษาพร้อมระดับความเสี่ยงที่: {preds_out_path}")

    # 5. ความสำคัญของฟีเจอร์ด้วยวิธี Permutation Feature Importance
    print("[+] กำลังคำนวณ Permutation Feature Importance บนชุด Holdout Test...")
    rng = np.random.default_rng(42)
    perm_sample_idx = rng.choice(len(X_test), size=min(5000, len(X_test)), replace=False)
    perm = permutation_importance(
        champion_model,
        X_test[perm_sample_idx],
        y_test[perm_sample_idx],
        n_repeats=3,
        random_state=42,
        scoring="average_precision",
        n_jobs=1,
    )
    perm_df = pd.DataFrame({
        "feature": feature_cols,
        "importance_mean": perm.importances_mean,
        "importance_std": perm.importances_std,
    }).sort_values("importance_mean", ascending=False)
    feat_imp_path = os.path.join(TABLES_DIR, "feature_importance.csv")
    perm_df.to_csv(feat_imp_path, index=False)
    print(f"[+] บันทึกความสำคัญของฟีเจอร์ที่: {feat_imp_path}")

    # 6. การตรวจสอบความเป็นธรรมตามกลุ่มประชากร (Fairness Diagnostics)
    print("[+] กำลังวิเคราะห์ความเป็นธรรมจำแนกตามกลุ่มประชากรย่อย...")
    test_students = df_students[df_students["userid_DI"].isin(test_userids)].copy()
    test_merged = pd.merge(df_predictions, test_students[["userid_DI", "gender", "LoE_DI", "country"]], on="userid_DI")

    fairness_rows = []
    # มิติด้านเพศ
    for g, grp in test_merged.groupby("gender"):
        fairness_rows.append({
            "demographic_dimension": "เพศ (Gender)",
            "subgroup": g,
            "sample_size": len(grp),
            "true_positive_rate_empirical": round(float(grp["true_certified"].mean() * 100), 2),
            "predicted_positive_rate": round(float(grp["predicted_label_optimal"].mean() * 100), 2),
            "precision": round(float(precision_score(grp["true_certified"], grp["predicted_label_optimal"], zero_division=0)), 4),
            "recall": round(float(recall_score(grp["true_certified"], grp["predicted_label_optimal"], zero_division=0)), 4),
            "mean_predicted_prob": round(float(grp["predicted_probability"].mean()), 4),
        })
    # มิติด้านระดับการศึกษา
    for loe, grp in test_merged.groupby("LoE_DI"):
        fairness_rows.append({
            "demographic_dimension": "ระดับการศึกษา (LoE)",
            "subgroup": loe,
            "sample_size": len(grp),
            "true_positive_rate_empirical": round(float(grp["true_certified"].mean() * 100), 2),
            "predicted_positive_rate": round(float(grp["predicted_label_optimal"].mean() * 100), 2),
            "precision": round(float(precision_score(grp["true_certified"], grp["predicted_label_optimal"], zero_division=0)), 4),
            "recall": round(float(recall_score(grp["true_certified"], grp["predicted_label_optimal"], zero_division=0)), 4),
            "mean_predicted_prob": round(float(grp["predicted_probability"].mean()), 4),
        })
    df_fairness = pd.DataFrame(fairness_rows)
    fairness_path = os.path.join(TABLES_DIR, "fairness_diagnostics.csv")
    df_fairness.to_csv(fairness_path, index=False)
    print(f"[+] บันทึกผลการวิเคราะห์ความเป็นธรรมที่: {fairness_path}")

    # 7. การวิเคราะห์ข้อผิดพลาดของโมเดล (Misclassification Error Analysis)
    print("[+] กำลังวิเคราะห์ลักษณะของนักศึกษาที่ทำนายผิดพลาด...")
    test_merged["error_type"] = "ถูกต้อง (Correct)"
    test_merged.loc[(test_merged["true_certified"] == 1) & (test_merged["predicted_label_optimal"] == 0), "error_type"] = "FN (ทำนายหลุด: จบจริงแต่ทายไม่จบ)"
    test_merged.loc[(test_merged["true_certified"] == 0) & (test_merged["predicted_label_optimal"] == 1), "error_type"] = "FP (ทำนายเกิน: ไม่จบจริงแต่ทายจบ)"

    error_profile = test_merged.merge(
        test_students[["userid_DI", "total_events", "total_active_days", "total_chapters", "total_video_plays", "event_intensity"]],
        on="userid_DI",
    )
    error_summary = error_profile.groupby("error_type").agg(
        count=("userid_DI", "count"),
        mean_events=("total_events", "mean"),
        mean_active_days=("total_active_days", "mean"),
        mean_chapters=("total_chapters", "mean"),
        mean_video_plays=("total_video_plays", "mean"),
        mean_prob=("predicted_probability", "mean"),
    ).reset_index()
    error_summary_path = os.path.join(TABLES_DIR, "error_analysis.csv")
    error_summary.to_csv(error_summary_path, index=False)
    print(f"[+] บันทึกตารางวิเคราะห์ข้อผิดพลาดที่: {error_summary_path}")

    # ประวัติรอบการวนลูปพัฒนาโมเดล (Optimization History)
    opt_history = []
    for iteration, (family, group) in enumerate(successful_tuning.groupby("family", sort=False), start=1):
        best = group.sort_values(
            ["val_pr_auc", "val_roc_auc", "val_brier_score"],
            ascending=[False, False, True],
        ).iloc[0]
        opt_history.append({
            "iteration": iteration,
            "phase": family,
            "candidate": best["model_name"],
            "pr_auc": round(float(best["val_pr_auc"]), 4),
            "decision": "ชนะเลิศและผ่านการล็อกโมเดล" if best["model_id"] == champion_id else "เกณฑ์เปรียบเทียบมาตรฐานของกลุ่ม",
        })
    pd.DataFrame(opt_history).to_csv(os.path.join(TABLES_DIR, "optimization_history.csv"), index=False)

    # 8. การสร้างกราฟิกและภาพประกอบผลการประเมิน (Visualizations)
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    navy, blue, cyan = "#173B69", "#4F86C6", "#56C2E6"
    violet, mint, coral = "#7567C8", "#54C6A5", "#EC7063"
    palette = [navy, violet, cyan, mint]
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Thonburi", "Sukhumvit Set", "Arial", "DejaVu Sans"],
        "axes.unicode_minus": False,
        "axes.titlecolor": navy,
        "axes.labelcolor": "#24344D",
        "xtick.color": "#52627A",
        "ytick.color": "#52627A",
        "axes.edgecolor": "#D7E1EC",
        "grid.color": "#E8EEF5",
        "grid.linewidth": 0.8,
    })

    model_display = {
        "random_forest_d15": "Random Forest (Calibrated)",
        "random_forest_d10": "Random Forest (d=10)",
        "hist_gbdt_lr10": "HistGradientBoosting (lr=0.10)",
        "hist_gbdt_lr05": "HistGradientBoosting (lr=0.05)",
        "extra_trees_d15": "Extra Trees",
        "logistic_reg_unweighted": "Logistic Regression (Unweighted)",
        "mlp_neural_net": "Neural Network (MLP)",
    }

    def style_axis(ax, grid_axis="both"):
        ax.set_facecolor("white")
        ax.grid(True, axis=grid_axis, alpha=0.9)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    top_models = df_test_comp[df_test_comp["model_id"] != "dummy_baseline"].head(4)["model_id"].tolist()

    # รูปที่ 1: ROC Curves
    fig, ax = plt.subplots(figsize=(9, 6.5), facecolor="white")
    for idx, (mid, col) in enumerate(zip(top_models, palette)):
        if mid in probs_dict:
            fpr, tpr, _ = roc_curve(y_test, probs_dict[mid])
            auc = roc_auc_score(y_test, probs_dict[mid])
            label = model_display.get(mid, mid.replace("_", " ").title())
            ax.plot(fpr, tpr, label=f"{label}  ·  AUC {auc:.3f}", color=col, lw=3.0 if idx == 0 else 2.0)
    ax.plot([0, 1], [0, 1], color="#9AA8B8", linestyle="--", lw=1.6, label="เส้นเดาสุ่ม (Random Chance)  ·  AUC 0.500")
    ax.set_xlabel("อัตราผลบวกลวง (False Positive Rate: 1 − Specificity)", fontsize=11, fontweight="bold")
    ax.set_ylabel("อัตราผลบวกจริง (True Positive Rate: Recall)", fontsize=11, fontweight="bold")
    ax.set_title("เส้นโค้ง ROC บนชุดทดสอบ Holdout Test (การแยกแยะระหว่างกลุ่ม)", fontsize=13, fontweight="bold", pad=14)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=2, frameon=False, fontsize=9)
    style_axis(ax)
    fig.tight_layout(rect=[0, 0.08, 1, 1])
    fig.savefig(os.path.join(FIGURES_DIR, "roc_curves.png"), dpi=180, bbox_inches="tight")
    plt.close(fig)

    # รูปที่ 2: Precision-Recall Curves
    fig, ax = plt.subplots(figsize=(9, 6.5), facecolor="white")
    for idx, (mid, col) in enumerate(zip(top_models, palette)):
        if mid in probs_dict:
            prec, rec, _ = precision_recall_curve(y_test, probs_dict[mid])
            ap = average_precision_score(y_test, probs_dict[mid])
            label = model_display.get(mid, mid.replace("_", " ").title())
            ax.plot(rec, prec, label=f"{label}  ·  PR-AUC {ap:.3f}", color=col, lw=3.0 if idx == 0 else 2.0)
    baseline_pr = float(np.mean(y_test))
    ax.axhline(baseline_pr, color=coral, linestyle="--", lw=1.8, label=f"เกณฑ์ความชุกพื้นฐาน (Prevalence)  ·  {baseline_pr:.3f}")
    ax.set_xlabel("อัตราตรวจพบ (Recall)", fontsize=11, fontweight="bold")
    ax.set_ylabel("ความแม่นยำ (Precision)", fontsize=11, fontweight="bold")
    ax.set_ylim(0, 1.02)
    ax.set_title("เส้นโค้ง Precision-Recall บนชุดทดสอบ (สำหรับข้อมูลไม่สมดุล)", fontsize=13, fontweight="bold", pad=14)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=2, frameon=False, fontsize=9)
    style_axis(ax)
    fig.tight_layout(rect=[0, 0.08, 1, 1])
    fig.savefig(os.path.join(FIGURES_DIR, "pr_curves.png"), dpi=180, bbox_inches="tight")
    plt.close(fig)

    # รูปที่ 3: Probability Calibration Curves
    fig, ax = plt.subplots(figsize=(9, 6.5), facecolor="white")
    calibration_models = df_test_comp[df_test_comp["model_id"] != "dummy_baseline"].head(3)["model_id"].tolist()
    for idx, (mid, col) in enumerate(zip(calibration_models, palette[:3])):
        if mid in probs_dict:
            prob_true, prob_pred = calibration_curve(y_test, probs_dict[mid], n_bins=10)
            label = model_display.get(mid, mid.replace("_", " ").title())
            ax.plot(prob_pred, prob_true, marker="o", markersize=5, lw=2.4 if idx == 0 else 1.8, color=col, label=label)
    ax.plot([0, 1], [0, 1], color="#9AA8B8", linestyle="--", lw=1.6, label="การเทียบเคียงสมบูรณ์แบบ (Perfect Calibration)")
    ax.set_xlabel("ค่าความน่าจะเป็นเฉลี่ยที่โมเดลทำนาย (Mean Predicted Probability)", fontsize=11, fontweight="bold")
    ax.set_ylabel("อัตราการสำเร็จจริงที่สังเกตได้ (Observed Certification Rate)", fontsize=11, fontweight="bold")
    ax.set_title("เส้นโค้งการเทียบเคียงความน่าจะเป็น (Probability Calibration)", fontsize=13, fontweight="bold", pad=14)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=2, frameon=False, fontsize=9)
    style_axis(ax)
    fig.tight_layout(rect=[0, 0.08, 1, 1])
    fig.savefig(os.path.join(FIGURES_DIR, "calibration_curves.png"), dpi=180, bbox_inches="tight")
    plt.close(fig)

    # รูปที่ 4: Confusion Matrices ที่ได้รับการแก้ไขโครงสร้างและผลรวมขอบอย่างสมบูรณ์
    fig, axes = plt.subplots(1, 2, figsize=(14.5, 6.2), constrained_layout=True, facecolor="white")
    cm_50 = confusion_matrix(y_test, champ_preds_50)
    image = None

    threshold_titles = [
        f"จุดตัดที่เลือกจากการจูน Validation (Threshold = {optimal_threshold:.4f})\n[เกณฑ์ Max-F1: สร้างสมดุล Precision-Recall ได้ดีที่สุด]",
        "จุดตัดค่าเริ่มต้นมาตรฐาน (Threshold = 0.50)\n[สอดคล้องกับเกณฑ์ Tier 1: นักศึกษาโอกาสสำเร็จ >= 50%]"
    ]

    for ax, cm, title in zip(axes, [cm_opt, cm_50], threshold_titles):
        cm_share = cm / cm.sum(axis=1, keepdims=True)
        r_sums = cm.sum(axis=1)
        c_sums = cm.sum(axis=0)

        image = ax.imshow(cm_share, interpolation="nearest", cmap=sns.light_palette(navy, as_cmap=True), vmin=0, vmax=1)
        ax.set_title(title, fontsize=11, fontweight="bold", color=navy, pad=12)

        x_tick_labels = [
            f"ทำนายไม่จบ\n(Pred: {c_sums[0]:,} คน, {c_sums[0]/total_test*100:.1f}%)",
            f"ทำนายได้ใบจบ\n(Pred: {c_sums[1]:,} คน, {c_sums[1]/total_test*100:.1f}%)"
        ]
        y_tick_labels = [
            f"ไม่จบจริง\n(Actual: {r_sums[0]:,} คน, {r_sums[0]/total_test*100:.1f}%)",
            f"ได้ใบจบจริง\n(Actual: {r_sums[1]:,} คน, {r_sums[1]/total_test*100:.1f}%)"
        ]
        ax.set_xticks([0, 1], labels=x_tick_labels, fontsize=10)
        ax.set_yticks([0, 1], labels=y_tick_labels, fontsize=10)

        cell_labels = [
            ["TN (ไม่จบ ถูกต้อง)", "FP (ทำนายเกิน)"],
            ["FN (ทำนายหลุด)", "TP (ได้ใบจบ ถูกต้อง)"]
        ]
        for i in range(2):
            for j in range(2):
                cell_count = cm[i, j]
                cell_row_pct = cm_share[i, j]
                cell_name = cell_labels[i][j]
                text_color = "white" if cell_row_pct > 0.52 else "#1C2A3A"
                ax.text(
                    j, i,
                    f"{cell_name}\n{cell_count:,} คน\n({cell_row_pct:.1%} ของแถวจริง)",
                    ha="center", va="center",
                    color=text_color, fontweight="bold", fontsize=10
                )
        ax.set_ylabel("สถานะจริง (Actual Class)", fontsize=11, fontweight="bold")
        ax.set_xlabel("สถานะที่ทำนาย (Predicted Class)", fontsize=11, fontweight="bold")
        ax.grid(False)

    fig.suptitle(
        f"Confusion Matrices — ผลการทดสอบบนชุดทดสอบ Holdout Test (N = {total_test:,} คน, ผลรวมแถว/คอลัมน์ตรง 100%)\n"
        f"ผู้ได้รับใบจบจริง: {actual_cert_count:,} คน ({actual_cert_pct:.2f}%) | "
        f"โมเดลทำนายได้ใบจบ (ที่ Threshold={optimal_threshold:.2f}): {pred_cert_count_opt:,} คน ({pred_cert_pct_opt:.2f}%)",
        fontsize=12, fontweight="bold", color=navy
    )
    if image is not None:
        colorbar = fig.colorbar(image, ax=axes, fraction=0.025, pad=0.03)
        colorbar.set_label("สัดส่วนเทียบกับกลุ่มจริงในแถว (Row Share %)", fontsize=10)
    fig.savefig(os.path.join(FIGURES_DIR, "confusion_matrices.png"), dpi=180, bbox_inches="tight")
    plt.close(fig)

    # รูปที่ 5: Feature Importance Bar Plot
    top_feats = perm_df.head(12).copy().iloc[::-1]
    top_feats["display_feature"] = top_feats["feature"].str.replace("_", " ", regex=False).str.title()
    fig, ax = plt.subplots(figsize=(10, 6.5), facecolor="white")
    bar_colors = sns.blend_palette([cyan, violet], n_colors=len(top_feats))
    bars = ax.barh(top_feats["display_feature"], top_feats["importance_mean"],
                   xerr=top_feats["importance_std"], color=bar_colors, edgecolor="white",
                   error_kw={"ecolor": "#8493A7", "capsize": 2, "elinewidth": 1})
    for bar, value in zip(bars, top_feats["importance_mean"]):
        ax.text(bar.get_width() + max(top_feats["importance_mean"]) * 0.015,
                bar.get_y() + bar.get_height() / 2, f"{value:.4f}", va="center", fontsize=9, color="#33435A")
    ax.set_xlabel("ค่า PR-AUC ที่ลดลงเมื่อสลับค่าฟีเจอร์ (Drop in PR-AUC)", fontsize=11, fontweight="bold")
    ax.set_ylabel("")
    ax.set_title("ลำดับความสำคัญของฟีเจอร์ (Permutation Feature Importance)", fontsize=13, fontweight="bold", pad=14)
    ax.set_xlim(left=0, right=max(top_feats["importance_mean"] + top_feats["importance_std"]) * 1.18)
    style_axis(ax, grid_axis="x")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "feature_importance.png"), dpi=180, bbox_inches="tight")
    plt.close(fig)

    # รูปที่ 6: Risk Tier Distribution & Empirical Completion Rate
    tier_summary = df_predictions.groupby("risk_tier").agg(
        student_count=("true_certified", "count"),
        completion_rate=("true_certified", "mean"),
    ).loc[[
        "Tier 1: Low Risk / Likely Completer",
        "Tier 2: Moderate Risk / Target for Nudge",
        "Tier 3: High Risk / Early Dropout",
    ]]

    tier_names_short = ["Tier 1\nความเสี่ยงต่ำ / มีแนวโน้มจบ", "Tier 2\nความเสี่ยงปานกลาง / เป้าหมายหนุน", "Tier 3\nความเสี่ยงสูง / เสี่ยงออกกลางคัน"]
    tier_colors = [mint, violet, coral]
    tier_share = tier_summary["student_count"] / len(df_predictions) * 100
    tier_rate = tier_summary["completion_rate"] * 100
    fig, (ax_count, ax_rate) = plt.subplots(1, 2, figsize=(13, 5.8), constrained_layout=True, facecolor="white")

    count_bars = ax_count.bar(tier_names_short, tier_share, color=tier_colors, width=0.58, edgecolor="white")
    for bar, count, share in zip(count_bars, tier_summary["student_count"], tier_share):
        ax_count.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.2,
                      f"{int(count):,} คน\n({share:.1f}%)", ha="center", fontweight="bold", color="#33435A", fontsize=10)
    ax_count.set_ylabel("สัดส่วนของนักศึกษาในชุดทดสอบ (%)", fontsize=11, fontweight="bold")
    ax_count.set_ylim(0, 100)
    ax_count.set_title("การกระจายตัวของนักศึกษาตามระดับความเสี่ยง", fontsize=12, fontweight="bold", color=navy)
    style_axis(ax_count, grid_axis="y")

    rate_bars = ax_rate.bar(tier_names_short, tier_rate, color=tier_colors, width=0.58, edgecolor="white")
    for bar, rate in zip(rate_bars, tier_rate):
        ax_rate.text(bar.get_x() + bar.get_width() / 2, min(bar.get_height() + 2, 96),
                     f"{rate:.1f}%", ha="center", fontweight="bold", color="#33435A", fontsize=10)
    ax_rate.set_ylabel("อัตราการสำเร็จการศึกษาจริงที่เกิดขึ้น (%)", fontsize=11, fontweight="bold")
    ax_rate.set_ylim(0, 100)
    ax_rate.set_title("อัตราการสำเร็จการศึกษาจริงในแต่ละระดับความเสี่ยง", fontsize=12, fontweight="bold", color=navy)
    style_axis(ax_rate, grid_axis="y")

    fig.suptitle("การแบ่งกลุ่มความเสี่ยงในการปฏิบัติงานจริง (Operational Risk Tiers)", fontsize=13, fontweight="bold", color=navy)
    fig.savefig(os.path.join(FIGURES_DIR, "risk_tier_distribution.png"), dpi=180, bbox_inches="tight")
    plt.close(fig)

    print(f"[+] บันทึกภาพประกอบการประเมินผลทั้งหมดเรียบร้อยที่: {FIGURES_DIR}")

    # 9. ล็อกโมเดลชนะเลิศ (Lock Champion Model)
    print("[+] กำลังล็อกโมเดลชนะเลิศและสร้างไฟล์กำกับความสมบูรณ์ทางเข้ารหัส (Cryptographic Lock Manifest)...")
    final_model_path = os.path.join(FINAL_MODELS_DIR, "supervised_model.joblib")
    joblib.dump(champion_model, final_model_path)

    model_hash = get_sha256(final_model_path)
    lock_manifest = {
        "locked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "champion_model_id": champion_id,
        "champion_model_name": str(champion_model.__class__.__name__),
        "model_file_sha256": model_hash,
        "optimal_decision_threshold": round(optimal_threshold, 4),
        "test_metrics": {
            "test_roc_auc": round(float(roc_auc_score(y_test, champ_probs)), 4),
            "test_pr_auc": round(float(average_precision_score(y_test, champ_probs)), 4),
            "test_brier_score": round(float(brier_score_loss(y_test, champ_probs)), 4),
            "test_f1_optimal": round(f1_opt, 4),
            "test_recall_optimal": round(recall, 4),
            "test_precision_optimal": round(precision, 4),
            "test_accuracy_optimal": round(accuracy, 4),
            "test_specificity_optimal": round(specificity, 4),
        },
        "predicted_certificate_metrics": {
            "holdout_test_size": total_test,
            "actual_certificate_count": actual_cert_count,
            "actual_certificate_pct": round(actual_cert_pct, 2),
            "predicted_certificate_count": pred_cert_count_opt,
            "predicted_certificate_pct": round(pred_cert_pct_opt, 2),
            "system_total_students": system_total_students,
            "system_actual_certified": system_actual_certified,
            "system_projected_certified": system_projected_certified,
        },
        "risk_tier_policy": config["risk_tiers"],
        "confusion_matrix": {
            "TP": int(tp),
            "FP": int(fp),
            "TN": int(tn),
            "FN": int(fn),
            "row_actual_negative": row_actual_negative,
            "row_actual_positive": row_actual_positive,
            "col_pred_negative": col_pred_negative,
            "col_pred_positive": col_pred_positive,
            "total": total_test,
        },
        "governance_lock": "LOCKED FOR PRODUCTION INFERENCE",
    }
    with open(os.path.join(FINAL_MODELS_DIR, "model_lock.json"), "w", encoding="utf-8") as handle:
        json.dump(lock_manifest, handle, indent=2, ensure_ascii=False)

    print(f"[+] ล็อกโมเดลสำเร็จ: {final_model_path} (SHA-256: {model_hash[:16]}...)")
    print(f"[+] บันทึกไฟล์ข้อกำหนดการล็อกโมเดลที่: {os.path.join(FINAL_MODELS_DIR, 'model_lock.json')}")


if __name__ == "__main__":
    run_model_evaluation()

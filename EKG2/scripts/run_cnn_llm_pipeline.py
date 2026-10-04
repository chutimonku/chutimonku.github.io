#!/usr/bin/env python3
"""
scripts/run_cnn_llm_pipeline.py
================================
Executes the end-to-end Multimodal 1D-CNN + Clinical LLM Pipeline on PTB-XL ECG Cohort.

Workflow:
1. Loads 1D-CNN (Hierarchical ResNet1D-500Hz) weights from outputs/models/cnn_1d_500hz.pt.
2. Selects multi-visit and diverse diagnostic cohorts from PTB-XL database.
3. Performs 500 Hz DSP filtering (Butterworth 0.5-45 Hz + 50 Hz Notch).
4. Runs 1D-CNN inference to obtain:
   - Stage 1: Binary screening probabilities (Normal vs Abnormal).
   - Stage 2: 5-class differential probabilities (NORM, MI, STTC, CD, HYP).
   - 256-dimensional deep latent feature embeddings.
   - Spatial-temporal 1D-CAM (Grad-CAM) class activation weights.
5. Extracts clinical EKG biomarkers (Heart Rate, QRS duration, PR interval, QTc, Hexaxial Axis, ST elevation).
6. Runs Clinical LLM Copilot to synthesize:
   - Structured Clinical ECG Diagnostic Reports (Bilingual: Thai & English).
   - Pathophysiological mechanisms explaining why the CNN made the prediction.
   - AHA/ACC Guideline-directed Triage & Medical Recommendations.
   - Longitudinal trajectory deltas across sequential patient visits.
7. Saves results to outputs/evaluation/cnn_llm_clinical_reports.json.
"""

import os
import sys
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd
import wfdb

# Add project root and src to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from cnn_llm_engine import ECGLLMEngine, CLASS_NAMES, CLASS_DESCRIPTIONS

def main():
    print("=" * 80)
    print("🚀 STARTING MULTIMODAL 1D-CNN + CLINICAL LLM PIPELINE EXECUTION")
    print("=" * 80)

    data_dir = project_root / "ptb-xl-a-large-publicly-available-electrocardiography-dataset-1.0.3"
    db_csv = data_dir / "ptbxl_database.csv"
    model_pt = project_root / "outputs" / "models" / "cnn_1d_500hz.pt"
    out_json = project_root / "outputs" / "evaluation" / "cnn_llm_clinical_reports.json"

    if not db_csv.exists():
        print(f"❌ Error: Database not found at {db_csv}")
        return

    df = pd.read_csv(db_csv)
    print(f"✅ Loaded PTB-XL database: {len(df):,} records, {df['patient_id'].nunique():,} unique patients.")

    # Initialize CNN + LLM Engine
    print(f"🧠 Initializing 1D-CNN & Clinical LLM Engine...")
    engine = ECGLLMEngine(model_path=str(model_pt), device="cpu")

    # Select representative cohort (focused on multi-visit patients & all 5 diagnostic superclasses)
    multi_pts = df[df.groupby('patient_id')['patient_id'].transform('count') >= 2]['patient_id'].unique()
    selected_pids = [21602.0, 8304.0, 307.0, 15765.0, 9898.0, 319.0, 318.0, 8810.0, 10107.0, 13145.0, 20655.0, 302.0]
    
    # Filter records
    cohort_df = df[df['patient_id'].isin(selected_pids)].copy()
    cohort_df['recording_date'] = pd.to_datetime(cohort_df['recording_date'])
    cohort_df = cohort_df.sort_values(['patient_id', 'recording_date'])

    print(f"📊 Selected {cohort_df['patient_id'].nunique()} multi-visit patients with {len(cohort_df)} clinical encounters.")

    execution_results = {
        "pipeline_metadata": {
            "title": "Multimodal 1D-CNN + Clinical LLM Longitudinal Inference Registry",
            "model_architecture": "Hierarchical ResNet1D-500Hz + Clinical LLM Reasoning Engine",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_patients": int(cohort_df['patient_id'].nunique()),
            "total_encounters_processed": int(len(cohort_df)),
            "sampling_rate": "500 Hz (DSP Filtered: 0.5-45 Hz Bandpass + 50 Hz Notch)"
        },
        "patients": {}
    }

    start_total_time = time.time()
    processed_count = 0
    inference_latencies = []

    for pid, group in cohort_df.groupby('patient_id'):
        pid_str = str(int(pid))
        execution_results["patients"][pid_str] = {
            "patient_id": int(pid),
            "total_visits": len(group),
            "encounters": []
        }

        prev_enc_summary = None

        for _, row in group.iterrows():
            ecg_id = int(row['ecg_id'])
            rec_date = str(row['recording_date'])[:10]
            rel_file = row['filename_hr']
            full_record_path = str(data_dir / rel_file)

            # 1. Read raw 500 Hz waveform
            t0 = time.time()
            try:
                sig_5000x12, meta = wfdb.rdsamp(full_record_path)
            except Exception as e:
                print(f"⚠️ Error reading WFDB record {full_record_path}: {e}")
                continue

            # 2. Run 1D-CNN Inference + 1D-CAM
            cnn_res = engine.run_cnn_inference(sig_5000x12)
            t_inf = (time.time() - t0) * 1000.0 # ms
            inference_latencies.append(t_inf)

            # 3. Extract Clinical Vitals
            vitals = engine.extract_clinical_vitals(sig_5000x12)

            # 4. Prepare Demographics
            bmi_val = round(float(row['weight']) / ((float(row['height']) / 100.0) ** 2), 1) if pd.notnull(row['height']) and pd.notnull(row['weight']) and float(row['height']) > 0 else 25.4
            pt_demog = {
                'patient_id': int(pid),
                'ecg_id': ecg_id,
                'age': int(row['age']) if pd.notnull(row['age']) else 60,
                'sex': int(row['sex']) if pd.notnull(row['sex']) else 1,
                'bmi': bmi_val,
                'recording_date': rec_date,
                'original_physician_report': str(row['report']) if pd.notnull(row['report']) else 'None'
            }

            # 5. Generate LLM Reports (Thai & English)
            report_th = engine.generate_clinical_llm_report(pt_demog, cnn_res, vitals, previous_encounter=prev_enc_summary, lang='th')
            report_en = engine.generate_clinical_llm_report(pt_demog, cnn_res, vitals, previous_encounter=prev_enc_summary, lang='en')

            # 6. Sample clinical Q&A response
            sample_qa = {
                "question_th": "คนไข้รายนี้เสี่ยงระดับไหน และโมเดลตัดสินจากอะไร?",
                "answer_th": engine.answer_clinical_query("ทำไมโมเดลถึงตัดสินแบบนี้ และอันตรายไหม?", pt_demog, cnn_res, vitals, lang='th'),
                "question_en": "What is the clinical urgency and basis for this diagnosis?",
                "answer_en": engine.answer_clinical_query("What is the clinical basis and management?", pt_demog, cnn_res, vitals, lang='en')
            }

            enc_payload = {
                "ecg_id": ecg_id,
                "recording_date": rec_date,
                "demographics": pt_demog,
                "cnn_inference": {
                    "predicted_class": cnn_res['predicted_class'],
                    "confidence_pct": round(cnn_res['confidence'] * 100, 1),
                    "binary_screening": cnn_res['binary_probabilities'],
                    "multiclass_probabilities": cnn_res['multiclass_probabilities'],
                    "inference_latency_ms": round(t_inf, 2),
                    "gradcam_1d_summary": {
                        "length": len(cnn_res['gradcam_weights']),
                        "max_activation": float(np.max(cnn_res['gradcam_weights'])),
                        "mean_activation": float(np.mean(cnn_res['gradcam_weights']))
                    }
                },
                "clinical_vitals": vitals,
                "llm_cardiology_report_th": report_th,
                "llm_cardiology_report_en": report_en,
                "interactive_qa_sample": sample_qa
            }

            execution_results["patients"][pid_str]["encounters"].append(enc_payload)
            processed_count += 1

            # Update prev_enc_summary for longitudinal tracking in next visit
            prev_enc_summary = {
                'predicted_class': cnn_res['predicted_class'],
                'recording_date': rec_date,
                'heart_rate_bpm': vitals['heart_rate_bpm']
            }

            print(f"  [Pt #{pid_str} | Visit {rec_date}] 1D-CNN: {cnn_res['predicted_class']} ({round(cnn_res['confidence']*100,1)}%) | HR: {vitals['heart_rate_bpm']} bpm | Latency: {t_inf:.1f}ms | LLM Report ✅")

    # Add summary statistics
    execution_results["pipeline_metadata"]["avg_inference_latency_ms"] = round(float(np.mean(inference_latencies)), 2)
    execution_results["pipeline_metadata"]["total_execution_time_sec"] = round(time.time() - start_total_time, 2)

    # Save to JSON
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(execution_results, f, ensure_ascii=False, indent=2)

    print("=" * 80)
    print(f"🎉 PIPELINE COMPLETED SUCCESSFULLY!")
    print(f"📁 Results saved to: {out_json}")
    print(f"⚡ Total encounters processed: {processed_count}")
    print(f"⏱️ Average 1D-CNN Latency: {execution_results['pipeline_metadata']['avg_inference_latency_ms']} ms/record")
    print(f"⌛ Total Pipeline Runtime: {execution_results['pipeline_metadata']['total_execution_time_sec']} seconds")
    print("=" * 80)

if __name__ == "__main__":
    main()

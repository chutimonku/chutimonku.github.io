"""สคริปต์ Command-Line สำหรับทำนายความเสี่ยงและโอกาสสำเร็จการศึกษาของนักศึกษา MOOC."""

import argparse
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import joblib
import pandas as pd

PIPELINE_PATH = os.path.join("models", "final", "deployment_pipeline.joblib")


def main():
    parser = argparse.ArgumentParser(description="ทำนายความเสี่ยงและระดับความเสี่ยงของนักศึกษา MOOC (Student Completion Risk & Tier)")
    parser.add_argument("--input", "-i", required=True, help="ที่อยู่ไฟล์ CSV ข้อมูลโปรไฟล์นักศึกษา")
    parser.add_argument("--output", "-o", default="outputs/data/cli_predictions.csv", help="ที่อยู่สำหรับบันทึกไฟล์ผลการทำนาย CSV")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"ข้อผิดพลาด: ไม่พบไฟล์อินพุต '{args.input}'", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(PIPELINE_PATH):
        print(f"ข้อผิดพลาด: ไม่พบ Deployment Pipeline '{PIPELINE_PATH}' กรุณารันเวิร์กโฟลว์ก่อน", file=sys.stderr)
        sys.exit(1)

    print(f"[+] กำลังโหลด Deployment Pipeline จาก: {PIPELINE_PATH}")
    pipeline = joblib.load(PIPELINE_PATH)

    print(f"[+] กำลังอ่านข้อมูลนักศึกษาจาก: {args.input}")
    df_input = pd.read_csv(args.input)

    try:
        total_students = len(df_input)
        print(f"[+] กำลังประมวลผลทำนายนักศึกษาทั้งหมด {total_students:,} คน...")
        results = pipeline.predict_risk_tiers(df_input)
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        results.to_csv(args.output, index=False)
        print(f"[+] บันทึกผลการทำนายเรียบร้อยแล้วที่: {args.output}")

        # สรุปผลการทำนายและยืนยันจำนวนเด็กที่จะได้รับใบจบ
        n_cert_opt = int((results["completion_probability"] >= pipeline.optimal_threshold).sum())
        n_cert_50 = int((results["completion_probability"] >= 0.50).sum())
        n_dropout = int((results["completion_probability"] < 0.15).sum())

        print("\n" + "=" * 60)
        print("สรุปภาพรวมผลการทำนายประชากรนักศึกษา:")
        print("=" * 60)
        print(f"- นักศึกษาทั้งหมดที่ประเมิน: {total_students:,} คน")
        print(f"- คาดว่าจะได้รับใบจบ (เกณฑ์ Max-F1, Threshold={pipeline.optimal_threshold:.4f}): {n_cert_opt:,} คน ({n_cert_opt/total_students*100:.2f}%)")
        print(f"- มีแนวโน้มเรียนจบสูง (Tier 1: โอกาสจบ >= 50%): {n_cert_50:,} คน ({n_cert_50/total_students*100:.2f}%)")
        print(f"- ความเสี่ยงสูงเสี่ยงออกกลางคัน (Tier 3: โอกาสจบ < 15%): {n_dropout:,} คน ({n_dropout/total_students*100:.2f}%)")
        print("\nการแจกแจงตามระดับความเสี่ยง 3 กลุ่ม (Risk Tiers):")
        print(results["risk_tier"].value_counts())
        print("=" * 60)
    except Exception as e:
        print(f"\n[!] เกิดข้อผิดพลาดในการทำนาย (Inference Error): {str(e)}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()

"""เว็บแอปพลิเคชัน Streamlit สำหรับทำนายความเสี่ยงและโอกาสสำเร็จการศึกษาของนักศึกษา MOOC."""

from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

from src.deployment import DataLeakageSecurityException, InputSchemaError


PROJECT_ROOT = Path(__file__).resolve().parent
PIPELINE_PATH = PROJECT_ROOT / "models" / "final" / "deployment_pipeline.joblib"
SAMPLE_PATH = PROJECT_ROOT / "examples" / "sample_student_input.csv"


@st.cache_resource
def load_pipeline():
    """โหลด Deployment Pipeline ที่ผ่านการตรวจสอบและล็อกโมเดลเรียบร้อยแล้ว."""
    if not PIPELINE_PATH.exists():
        raise FileNotFoundError(
            "ไม่พบไฟล์ deployment_pipeline.joblib กรุณารันคำสั่ง python -m src.pipeline ก่อนใช้งาน"
        )
    return joblib.load(PIPELINE_PATH)


st.set_page_config(
    page_title="ระบบทำนายความเสี่ยงและโอกาสสำเร็จการศึกษา MOOC",
    page_icon="🎓",
    layout="wide",
)

st.title("🎓 ระบบทำนายความเสี่ยงและโอกาสได้รับใบประกาศนียบัตรนักศึกษา MOOC")
st.caption(
    "อัปโหลดไฟล์ข้อมูลพฤติกรรมระดับนักศึกษา เพื่อประเมินโอกาสสำเร็จการศึกษาและแบ่งกลุ่มความเสี่ยง 3 ระดับ "
    "โดยใช้โมเดล Random Forest ที่ผ่านการจูนพารามิเตอร์และล็อกความสมบูรณ์แล้ว"
)

try:
    pipeline = load_pipeline()
except Exception as exc:  # pragma: no cover
    st.error(f"เกิดข้อผิดพลาดในการโหลดโมเดล: {exc}")
    st.stop()

expected_columns = ["userid_DI", *pipeline.required_input_features]

left, right = st.columns([1.05, 0.95])
with left:
    st.subheader("1. เตรียมไฟล์ข้อมูล")
    st.write(
        "ข้อมูลต้องสรุปเป็น **1 แถวต่อนักศึกษา 1 คน (userid_DI)** และต้องมีคอลัมน์ครบตาม Schema ที่กำหนด "
        "ระบบจะปฏิเสธข้อมูลที่ไม่สมบูรณ์เพื่อป้องกันความผิดพลาดในการตัดสินใจ"
    )
    template = pd.DataFrame(columns=expected_columns).to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 ดาวน์โหลดไฟล์แม่แบบ CSV (Template)",
        data=template,
        file_name="student_risk_input_template.csv",
        mime="text/csv",
    )
    if SAMPLE_PATH.exists():
        st.download_button(
            "📄 ดาวน์โหลดตัวอย่างข้อมูลทดสอบ (Sample CSV)",
            data=SAMPLE_PATH.read_bytes(),
            file_name=SAMPLE_PATH.name,
            mime="text/csv",
        )

with right:
    st.subheader("⚠️ กฎและข้อกำหนดด้านความปลอดภัย (Data Governance)")
    st.markdown(
        """
        - **ห้ามมีตัวแปรผลลัพธ์ปลายทาง:** `certified`, `grade`, `explored`, `incomplete_flag` (ป้องกันข้อมูลรั่วไหล)
        - `userid_DI` ต้องไม่เป็นค่าว่างและไม่ซ้ำกัน
        - จำนวนกิจกรรมต้องเป็นตัวเลขและไม่ติดลบ
        - `view_rate` และ `video_data_available_rate` ต้องอยู่ระหว่าง 0–1
        """
    )

with st.expander(f"📋 ดูรายชื่อคอลัมน์ที่ระบบต้องการ ({len(expected_columns)} คอลัมน์)"):
    st.code(", ".join(expected_columns), language="text")

uploaded = st.file_uploader("2. อัปโหลดไฟล์ข้อมูลนักศึกษา (CSV)", type=["csv"])

if uploaded is not None:
    try:
        input_df = pd.read_csv(uploaded)
    except Exception as exc:
        st.error(f"อ่านไฟล์ CSV ไม่สำเร็จ: {exc}")
        st.stop()

    st.write(f"พบข้อมูลทั้งหมด **{len(input_df):,} แถว** และ **{len(input_df.columns):,} คอลัมน์**")
    st.dataframe(input_df.head(10), use_container_width=True)

    if st.button("🚀 ประมวลผลและทำนายผลการเรียน", type="primary"):
        try:
            predictions = pipeline.predict_risk_tiers(input_df)
        except (InputSchemaError, DataLeakageSecurityException) as exc:
            st.error(f"ข้อมูลไม่ผ่านการตรวจสอบความปลอดภัยหรือ Schema: {exc}")
        except Exception as exc:  # pragma: no cover
            st.exception(exc)
        else:
            total_scored = len(predictions)
            opt_thresh = pipeline.optimal_threshold
            
            # คำนวณจำนวนเด็กที่จะได้รับใบจบ
            n_cert_opt = int((predictions["completion_probability"] >= opt_thresh).sum())
            n_cert_50 = int((predictions["completion_probability"] >= 0.50).sum())
            n_dropout = int((predictions["completion_probability"] < 0.15).sum())

            st.success(f"ประมวลผลทำนายสำเร็จสำหรับนักศึกษาทั้งหมด {total_scored:,} คน")

            # แสดงสรุปยืนยันจำนวนเด็กที่จะได้รับใบจบ (Metric Cards)
            st.subheader("📊 สรุปผลยืนยันการสำเร็จการศึกษาและระดับความเสี่ยง")
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("นักศึกษาทั้งหมด", f"{total_scored:,} คน")
            col1.caption("ประชากรในไฟล์ที่อัปโหลด")
            
            col2.metric(
                "คาดว่าจะได้รับใบจบ (เกณฑ์แม่นยำสูง)",
                f"{n_cert_opt:,} คน",
                f"{n_cert_opt/total_scored*100:.1f}% ของทั้งหมด",
            )
            col2.caption(f"เกณฑ์ Max-F1 (Threshold={opt_thresh:.2f})")

            col3.metric(
                "แนวโน้มสำเร็จสูง (Tier 1)",
                f"{n_cert_50:,} คน",
                f"{n_cert_50/total_scored*100:.1f}% ของทั้งหมด",
            )
            col3.caption("โอกาสเรียนจบ >= 50%")

            col4.metric(
                "กลุ่มเสี่ยงสูง (Tier 3)",
                f"{n_dropout:,} คน",
                f"{n_dropout/total_scored*100:.1f}% ของทั้งหมด",
                delta_color="inverse",
            )
            col4.caption("โอกาสเรียนจบ < 15% (ต้องช่วยด่วน)")

            # กล่องอธิบายความแตกต่างของตัวเลข
            st.info(
                f"""
                💡 **ทำความเข้าใจผลการทำนาย:**
                - **คาดว่าจะได้รับใบจบ ({n_cert_opt:,} คน):** ตัดสินด้วยจุดตัดที่ปรับจูนให้ F1 สูงสุด (Threshold = {opt_thresh:.2f}) ให้ความแม่นยำ (Precision) สูงถึง 74.2% และอัตราตรวจพบ (Recall) 84.2%
                - **ผู้มีแนวโน้มเรียนจบ Tier 1 ({n_cert_50:,} คน):** นักศึกษาที่มีความน่าจะเป็นจะเรียนจบตั้งแต่ 50% ขึ้นไป เพื่อใช้วางแผนการสนับสนุนเชิงรุก
                - **สถิติอ้างอิงของระบบ MOOC ทั้งหมด:** ในประชากรนักศึกษา 335,650 คน มีผู้ได้รับใบจบจริง 13,881 คน (4.14%)
                """
            )

            # ตารางแจกแจงตามกลุ่มความเสี่ยง
            st.subheader("การแจกแจงตามกลุ่มความเสี่ยง 3 ระดับ")
            tier_summary = (
                predictions["risk_tier"]
                .value_counts()
                .rename_axis("ระดับความเสี่ยง (Risk Tier)")
                .reset_index(name="จำนวนนักศึกษา (คน)")
            )
            tier_summary["สัดส่วน (%)"] = (
                tier_summary["จำนวนนักศึกษา (คน)"] / total_scored * 100
            ).round(2)
            st.dataframe(tier_summary, use_container_width=True, hide_index=True)

            # รายละเอียดผลการทำนายรายบุคคล
            st.subheader("ตารางผลการทำนายรายบุคคล")
            st.dataframe(predictions, use_container_width=True, hide_index=True)

            st.download_button(
                "📥 ดาวน์โหลดผลการทำนายทั้งหมดเป็นไฟล์ CSV",
                data=predictions.to_csv(index=False).encode("utf-8"),
                file_name="student_risk_predictions.csv",
                mime="text/csv",
            )

            # ตารางอ้างอิง Confusion Matrix
            with st.expander("🔍 ดูข้อมูลอ้างอิง Confusion Matrix จากการประเมินระบบ"):
                st.markdown(
                    """
                    **ผลการประเมินบนชุดทดสอบ Holdout Test Set (50,348 คน หรือ 15% ของประชากรทั้งหมด):**
                    
                    | สถานะจริง (Actual) | ทำนายไม่จบ (Pred: 0) | ทำนายได้ใบจบ (Pred: 1) | รวมความจริง (Row Marginals) |
                    | :--- | :---: | :---: | :---: |
                    | **ไม่จบจริง (Non-completer)** | 47,657 คน (98.7%) | 609 คน (1.3%) | **48,266 คน (100%)** |
                    | **ได้รับใบจบจริง (Certified)** | 329 คน (15.8%) | 1,753 คน (84.2%) | **2,082 คน (100%)** |
                    | **รวมที่โมเดลทำนาย (Col Marginals)** | **47,986 คน** | **2,362 คน** | **รวมทั้งหมด 50,348 คน** |
                    
                    - **ทำไมผลรวมคอลัมน์ถึงไม่เท่า 2,082 คน?** เพราะโมเดลทำนายได้ใบจบ 2,362 คน (ทายถูก 1,753 คน และทายเกิน 609 คน)
                    - **ทำไมเปอร์เซ็นต์ในคอลัมน์บวกกันไม่ได้ 100%?** เพราะเปอร์เซ็นต์คำนวณตามแนวนอนเทียบกับกลุ่มจริงในแถว (Row Share) ไม่ใช่เทียบกับคอลัมน์
                    - **ประชากรทั้งระบบ:** มีนักศึกษา 335,650 คน ได้รับใบจบจริง 13,881 คน (4.14%)
                    """
                )

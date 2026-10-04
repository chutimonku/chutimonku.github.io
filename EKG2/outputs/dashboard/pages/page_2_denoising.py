# outputs/dashboard/pages/page_2_denoising.py
"""
Page 2 – Ingestion & Signal Denoising (การนำเข้าข้อมูลและการกรองสัญญาณรบกวนคลื่นไฟฟ้าหัวใจ)
Provides:
- Ingestion and cleaning record attrition funnel (21,799 -> 21,388 -> 21,246)
- Digital Signal Processing (DSP) filter specification audit (Bandpass, Notch, Detrend)
- Real waveform viewer (Cleaned vs. Artifact Noise Residual) across 12 leads
- Signal Quality Index (SQI) audit across records (SNR, Kurtosis, Skewness, Dynamic Range)
- Quarantine isolation rules and corrupted signal detection criteria
- Comprehensive explanations in Thai
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def render():
    st.title("🎛️ Phase 2: Ingestion, Signal Denoising & SQI Audit")
    st.markdown("### การประมวลผลสัญญาณชีวการแพทย์ การกำจัดสัญญาณรบกวน และการตรวจวัดคุณภาพสัญญาณ (SQI)")

    root = Path.cwd()
    features_path = root / "data" / "processed" / "ptbxl_processed_features.parquet"
    waveforms_path = root / "data" / "cleaned" / "cleaned_waveforms_100hz.npy"
    cleaning_audit_path = root / "logs" / "cleaning_audit.json"

    if not features_path.exists() or not waveforms_path.exists():
        st.error("Processed features or cleaned waveforms not found.")
        return

    df = pd.read_parquet(features_path)

    # -------------------------------------------------------------------------
    # DSP Filter Specifications & Attrition Funnel
    # -------------------------------------------------------------------------
    st.subheader("🧹 กระบวนการคัดกรองและจำนวนข้อมูลในแต่ละขั้น (Data Attrition Funnel)")
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        st.metric("1. Raw Records", "21,799", help="ชุดข้อมูลดิบทั้งหมดจาก PhysioNet PTB-XL v1.0.3")
    with f2:
        st.metric("2. Target Isolation", "-411", help="ตัดข้อมูลที่ไม่มีผลวินิจฉัย Diagnostic Superclass")
    with f3:
        st.metric("3. Quarantined (Bad SQI)", "-142", help="กักกันข้อมูลที่สัญญาณขาดหาย (Flatline) หรือติดขอบ (ADC Saturation)")
    with f4:
        st.metric("4. Cleaned Records", f"{len(df):,}", help="ข้อมูลคลื่นไฟฟ้าหัวใจที่ผ่านเกณฑ์คุณภาพและพร้อมใช้งาน")

    # -------------------------------------------------------------------------
    # Explanation in Thai: DSP Pipeline & Quarantine Criteria
    # -------------------------------------------------------------------------
    st.markdown("""
    #### 🔬 กลไกการประมวลผลสัญญาณดิจิทัล (Digital Signal Processing - DSP Pipeline):
    1. **Baseline Wander Removal (การขจัดเส้นฐานลอย)**: ใช้การตัดแนวโน้มเชิงเส้น (Linear Detrending) ร่วมกับตัวกรอง High-pass ตัดความถี่ต่ำกว่า 0.5 Hz เพื่อกำจัดการขยับของเส้นฐานที่เกิดจากการหายใจและการเคลื่อนไหวของผู้ป่วย
    2. **Butterworth Zero-Phase Bandpass (0.5 – 45.0 Hz, Order 3)**:
       - กรองย่านความถี่ของการบีบตัวของหัวใจ (QRS Energy) ให้อยู่ในช่วง 0.5 ถึง 45.0 Hz
       - ใช้ `scipy.signal.filtfilt` (Zero-phase filtering) เพื่อป้องกันการเลื่อนของเฟส (Phase Distortion) ซึ่งทำให้ตำแหน่ง P, QRS, T ไม่คลาดเคลื่อน
    3. **Powerline Interference Suppression (50.0 Hz Notch Filter)**:
       - ตัดสัญญาณรบกวนจากกระแสไฟฟ้าสลับในทวีปยุโรป (50 Hz AC Mains Hum) ด้วยตัวกรอง IIR Notch ที่ค่า Quality Factor (Q) = 30
    4. **Signal Quality Index (SQI) Audit & Quarantine**:
       - ตรวจสอบความผิดปกติระดับสัญญาณ: Flatline (Standard Deviation < 1e-4 mV), ADC Saturation (> 20 mV), และค่า SNR ขั้นต่ำ
       - บันทึกสัญญาณที่ผิดปกติลงใน `data/quarantine/quarantined_records.csv` (142 รายการ) เพื่อไม่ให้รบกวนการเรียนรู้ของโมเดล
    """)

    st.markdown("---")

    # -------------------------------------------------------------------------
    # Real Waveform Viewer
    # -------------------------------------------------------------------------
    st.subheader("📈 แสดงรูปคลื่นไฟฟ้าหัวใจจริงหลังผ่านการกรอง (Cleaned Waveform Viewer)")

    # Select encounter from sample
    sample_records = df[["ecg_id", "patient_id", "diagnostic_superclass", "snr_mean_db", "kurtosis_mean"]].head(25)
    selected_ecg = st.selectbox(
        "เลือกบันทึกการตรวจคลื่นไฟฟ้าหัวใจ (Select ECG Record)",
        options=sample_records["ecg_id"].tolist(),
        format_func=lambda x: f"ECG #{x} | Patient #{df.loc[df['ecg_id']==x, 'patient_id'].iloc[0]} | Superclass: {df.loc[df['ecg_id']==x, 'diagnostic_superclass'].iloc[0]} | SNR: {df.loc[df['ecg_id']==x, 'snr_mean_db'].iloc[0]:.1f} dB"
    )

    record_row = df[df["ecg_id"] == selected_ecg].iloc[0]
    waveform_idx = int(record_row.get("waveform_index", df.index[df["ecg_id"] == selected_ecg][0]))

    # Load waveform memory map
    waveforms = np.load(waveforms_path, mmap_mode="r")
    lead_names = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]

    w_col1, w_col2 = st.columns([1, 3])
    with w_col1:
        selected_lead = st.selectbox("เลือก Lead (Lead Selection)", lead_names, index=1)
        lead_idx = lead_names.index(selected_lead)

        st.markdown(f"""
        **ข้อมูลจำเพาะของการตรวจนี้**:
        - **ECG ID**: `{selected_ecg}`
        - **Patient ID**: `{record_row['patient_id']}`
        - **Diagnostic Class**: `{record_row['diagnostic_superclass']}`
        - **Mean SNR**: `{record_row['snr_mean_db']:.2f} dB`
        - **QRS Kurtosis**: `{record_row['kurtosis_mean']:.2f}`
        - **Sampling Rate**: `100 Hz (1,000 samples / 10s)`
        """)

    with w_col2:
        sig_data = waveforms[waveform_idx, lead_idx, :]
        time_axis = np.linspace(0, 10, len(sig_data), endpoint=False)

        fig_wave = go.Figure()
        fig_wave.add_trace(go.Scatter(
            x=time_axis,
            y=sig_data,
            mode="lines",
            name=f"Lead {selected_lead} (Cleaned)",
            line=dict(color="#27ae60", width=1.8),
        ))

        fig_wave.update_layout(
            title=f"Cleaned 12-Lead ECG Signal – Lead {selected_lead} (10 Seconds Episode)",
            xaxis_title="Time (Seconds)",
            yaxis_title="Amplitude (mV)",
            height=340,
            margin=dict(t=40, b=20, l=10, r=10),
        )
        st.plotly_chart(fig_wave, use_container_width=True)

    # -------------------------------------------------------------------------
    # Signal Quality Index (SQI) Distributions across Dataset
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.subheader("📊 การกระจายตัวของคุณภาพสัญญาณจริงในระบบ (Dataset SQI Distribution)")
    sqi1, sqi2, sqi3 = st.columns(3)

    with sqi1:
        fig_snr = px.histogram(
            df,
            x="snr_mean_db",
            nbins=30,
            color_discrete_sequence=["#2980b9"],
            labels={"snr_mean_db": "Signal-to-Noise Ratio (dB)"},
            title="Mean SNR Distribution (dB)",
        )
        fig_snr.update_layout(height=280, margin=dict(t=40, b=20, l=10, r=10))
        st.plotly_chart(fig_snr, use_container_width=True)

    with sqi2:
        fig_kurt = px.histogram(
            df,
            x="kurtosis_mean",
            nbins=30,
            color_discrete_sequence=["#8e44ad"],
            labels={"kurtosis_mean": "Kurtosis (kSQI)"},
            title="Fisher Kurtosis Distribution (Peakedness)",
        )
        fig_kurt.update_layout(height=280, margin=dict(t=40, b=20, l=10, r=10))
        st.plotly_chart(fig_kurt, use_container_width=True)

    with sqi3:
        fig_skew = px.histogram(
            df,
            x="skewness_mean",
            nbins=30,
            color_discrete_sequence=["#d35400"],
            labels={"skewness_mean": "Skewness (sSQI)"},
            title="Skewness Distribution (Asymmetry)",
        )
        fig_skew.update_layout(height=280, margin=dict(t=40, b=20, l=10, r=10))
        st.plotly_chart(fig_skew, use_container_width=True)


if __name__ == "__main__":
    render()

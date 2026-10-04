# outputs/dashboard/app.py
"""Modular Streamlit dashboard for PTB‑XL longitudinal EKG analytics.

The dashboard is split into six page modules under the same package:
    page_governance.py   – Governance & Data Foundation (Page 1)
    page_denoising.py    – Ingestion & Signal Denoising (Page 2)
    page_features.py     – Feature Extraction & 8-Step Biomedical EDA (Page 3)
    page_model.py        – Model Training & Validation (Page 4)
    page_patient.py      – Patient Longitudinal Inspection & XAI (Page 5)
    page_6_cnn_llm.py    – Multimodal 1D-CNN + Clinical LLM Reasoning Copilot (Page 6)

Each module exports a single ``render()`` function that inserts its UI into the
current Streamlit container.
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st

# Import page modules – they live in the same directory
from outputs.dashboard.pages import (
    page_governance,
    page_denoising,
    page_features,
    page_model,
    page_patient,
    page_6_cnn_llm
)

# ---------------------------------------------------------------------------
# Sidebar Language Toggle & Navigation Configuration
# ---------------------------------------------------------------------------
lang = st.sidebar.radio("🌐 ภาษา / Language", ["🇹🇭 ภาษาไทย (เข้าใจง่าย)", "🇬🇧 English"], index=0)
is_th = "ภาษาไทย" in lang
st.session_state["selected_lang"] = "th" if is_th else "en"
st.session_state["lang"] = lang

PAGE_CONFIG_TH = [
    ("1. ข้อมูลตั้งต้น & ที่มา (Data Foundation)", "ข้อมูลตั้งต้น", page_governance),
    ("2. ล้างสัญญาณ EKG & ตรวจคุณภาพ (DSP Cleaning)", "การล้างสัญญาณ", page_denoising),
    ("3. สำรวจข้อมูลเชิงลึก 8 ขั้นตอน (EDA & Features)", "การวิเคราะห์ EDA", page_features),
    ("4. เปรียบเทียบประสิทธิภาพโมเดล AI (Model Benchmark)", "โมเดล AI & 1D-CNN", page_model),
    ("5. ดูประวัติคนไข้ & ตัวจำลองผลลัพธ์ (CDS Simulator)", "ประวัติคนไข้ & CDS", page_patient),
    ("6. รันโมเดล 1D-CNN & ผู้ช่วยแพทย์ LLM (Multimodal Copilot)", "1D-CNN & LLM Copilot", page_6_cnn_llm),
]

PAGE_CONFIG_EN = [
    ("1. Governance & Data Foundation", "Data Foundation", page_governance),
    ("2. Ingestion & Signal Denoising", "Signal Denoising", page_denoising),
    ("3. Feature Extraction & 8-Step EDA", "8-Step EDA", page_features),
    ("4. Model Training & Leaderboard", "Model Benchmarks", page_model),
    ("5. Patient Longitudinal View & CDS", "Patient CDS & Sim", page_patient),
    ("6. 1D-CNN & Clinical LLM Reasoning Copilot", "1D-CNN & LLM Copilot", page_6_cnn_llm),
]

page_config = PAGE_CONFIG_TH if is_th else PAGE_CONFIG_EN
page_labels = [item[0] for item in page_config]
short_labels = [item[1] for item in page_config]
page_modules = [item[2] for item in page_config]
total_pages = len(page_config)

# Handle programmatic page transitions from Next/Prev buttons
if "target_nav_idx" in st.session_state:
    st.session_state["nav_page_idx"] = st.session_state.pop("target_nav_idx")

if "nav_page_idx" not in st.session_state:
    st.session_state["nav_page_idx"] = 0

current_idx = max(0, min(total_pages - 1, st.session_state["nav_page_idx"]))
st.session_state["nav_page_idx"] = current_idx

if is_th:
    st.sidebar.title("⚡ PTB‑XL ระบบวิเคราะห์ EKG")
else:
    st.sidebar.title("⚡ PTB‑XL ECG Platform")

# Render Sidebar Radio
selected_label = st.sidebar.radio(
    "เลือกขั้นตอนการวิเคราะห์ (Pipeline)" if is_th else "Select Pipeline Stage",
    options=page_labels,
    index=current_idx,
)

# If user clicked the radio directly, update state
current_idx = page_labels.index(selected_label)
st.session_state["nav_page_idx"] = current_idx

# ---------------------------------------------------------------------------
# Render the chosen page
# ---------------------------------------------------------------------------
page_modules[current_idx].render()

# ---------------------------------------------------------------------------
# Global Navigation Footer: "Previous Page" & "Next Page" on EVERY page
# ---------------------------------------------------------------------------
st.markdown("---")
nav_container = st.container()
with nav_container:
    col_prev, col_info, col_next = st.columns([1, 2, 1])

    with col_prev:
        if current_idx > 0:
            prev_btn_text = "⬅️ ก่อนหน้า" if is_th else "⬅️ Previous"
            if st.button(prev_btn_text, use_container_width=True, key="btn_global_nav_prev"):
                st.session_state["target_nav_idx"] = current_idx - 1
                st.rerun()

    with col_info:
        st.markdown(
            f"<div style='text-align: center; color: #64748b; font-size: 0.90rem; padding-top: 6px; font-family: monospace;'>"
            f"{'ขั้นตอนที่' if is_th else 'Stage'} {current_idx + 1} / {total_pages}: <strong>{short_labels[current_idx]}</strong>"
            f"</div>",
            unsafe_allow_html=True
        )

    with col_next:
        if current_idx < total_pages - 1:
            next_btn_text = "หน้าถัดไป ➔" if is_th else "Next ➔"
            if st.button(next_btn_text, use_container_width=True, type="primary", key="btn_global_nav_next"):
                st.session_state["target_nav_idx"] = current_idx + 1
                st.rerun()
        else:
            restart_btn_text = "🔄 กลับหน้าแรก" if is_th else "🔄 Restart"
            if st.button(restart_btn_text, use_container_width=True, key="btn_global_nav_restart"):
                st.session_state["target_nav_idx"] = 0
                st.rerun()

# End of app.py
